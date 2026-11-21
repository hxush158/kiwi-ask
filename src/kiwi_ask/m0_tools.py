import json
import os
from datetime import date, datetime, timedelta
from typing import TypedDict, cast
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from pydantic import BaseModel, ConfigDict, ValidationError

from kiwi_ask.common.llm import get_chat_client

TOOLS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "check_rent_increase",
            "description": (
                "Check whether a proposed NZ residential rent increase "
                "meets the 12-month interval and 60-day notice requirements. "
                "Requires the previous increase date (or tenancy start) and notice date. "
                "If the proposed effective date is unknown, calculate the earliest "
                "effective date from the known dates and do not guess the missing date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "last_increase": {
                        "type": "string",
                        "description": (
                            "Date the previous rent increase took effect, or the "
                            "tenancy start date if rent has never been increased, "
                            "in YYYY-MM-DD format."
                        ),
                    },
                    "notice_date": {
                        "type": "string",
                        "description": (
                            "Date the notice for the proposed increase was given, "
                            "in YYYY-MM-DD format."
                        ),
                    },
                    "effective_date": {
                        "type": ["string", "null"],
                        "description": (
                            "Date the proposed rent increase would take effect, "
                            "in YYYY-MM-DD format. Omit it or pass null if unknown."
                        ),
                    },
                },
                "required": ["last_increase", "notice_date"],
                "additionalProperties": False,
            },
        },
    }
]


class RentIncreaseResult(TypedDict):
    allowed: bool | None
    earliest_effective_date: str
    notice_period_ok: bool | None
    reason: str


def check_rent_increase(
    last_increase: date, notice_date: date, effective_date: date | None = None
) -> RentIncreaseResult:
    # last_increase 也可以是首次涨租时的租赁开始日。
    # 假设：60 天按"通知日 + 60 天"计算，2 月 29 日加一年，取 2 月 28 日
    # 假设：不处理例外情况（房屋改善、Tribunal 申请）和固定期限租约。
    try:
        anniversary = last_increase.replace(year=last_increase.year + 1)
    except ValueError:
        if (last_increase.month, last_increase.day) != (2, 29):
            raise
        anniversary = last_increase.replace(year=last_increase.year + 1, day=28)

    notice_deadline = notice_date + timedelta(days=60)
    earliest_effective_date = max(anniversary, notice_deadline)
    if effective_date is None:
        return {
            "allowed": None,
            "earliest_effective_date": earliest_effective_date.isoformat(),
            "notice_period_ok": None,
            "reason": "未提供拟生效日，无法判断本次涨租是否满足这两项时间条件。",
        }

    notice_period_ok = effective_date >= notice_deadline

    reasons: list[str] = []
    if effective_date < anniversary:
        reasons.append(
            "拟生效日距上次涨租生效日（首次涨租则为租赁开始日）未满 12 个月。"
        )
    if not notice_period_ok:
        notice_days = (effective_date - notice_date).days
        reasons.append(f"通知日至拟生效日相隔 {notice_days} 天，未满 60 天。")

    return {
        "allowed": effective_date >= earliest_effective_date,
        "earliest_effective_date": earliest_effective_date.isoformat(),
        "notice_period_ok": notice_period_ok,
        "reason": " ".join(reasons) or "拟生效日满足 12 个月间隔和 60 天通知期。",
    }


MAX_ROUNDS = 3
QUESTIONS = [
    ("房东 8 个月前涨过租金，现在又通知要涨，合法吗？", True),
    (
        (
            "房东上次涨租于 2025 年 4 月 30 日生效，"
            "这次于 2026 年 3 月 2 日发通知，拟于 2026 年 4 月 30 日生效。"
            "符合涨租的时间要求吗？"
        ),
        True,
    ),
    ("新西兰租房押金（bond）是什么？", False),
]


class RentArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")

    last_increase: date
    notice_date: date
    effective_date: date | None = None


def run_tool_call(name: str, arguments: str) -> str:
    """Return the JSON content for a single tool reply."""
    if name != "check_rent_increase":
        return json.dumps({"error": "Unknown tool name."})

    try:
        args = RentArgs.model_validate_json(arguments)
    except ValidationError as exc:
        # Give the model the failing fields and reasons without echoing input.
        details = exc.errors(
            include_input=False, include_context=False, include_url=False
        )
        return json.dumps({"error": "Invalid tool arguments.", "details": details})

    try:
        result = check_rent_increase(
            last_increase=args.last_increase,
            notice_date=args.notice_date,
            effective_date=args.effective_date,
        )
    except (ValueError, OverflowError):
        return json.dumps(
            {
                "error": "last_increase or notice_date is outside the supported calculation range."
            }
        )

    return json.dumps(result, ensure_ascii=False)


def run_question(
    client: OpenAI, deployment: str, today: date, question: str
) -> bool | None:
    saw_tool_call = False
    messages: list[ChatCompletionMessageParam] = [
        {
            "role": "system",
            "content": (
                f"Today in New Zealand is {today.isoformat()}. "
                "Use this date to interpret relative dates. "
                "Convert relative dates (“8 months ago”, “now”) using today’s "
                "date and state the assumption. Ask only if no date can be inferred at all."
                "If the proposed effective date is missing, omit it or pass null. "
                "Use the tool for rent-increase timing checks when the required dates are known. "
                "Answer in Chinese. When using the tool, limit your conclusion "
                "to the timing requirements the tool checks."
            ),
        },
        {
            "role": "user",
            "content": question,
        },
    ]

    for round_number in range(1, MAX_ROUNDS + 1):
        response = client.chat.completions.create(
            model=deployment,
            messages=messages,
            tools=TOOLS,
            reasoning_effort="low",
            parallel_tool_calls=False,
            tool_choice="none" if round_number == MAX_ROUNDS else "auto",
        )

        if not response.choices:
            print("模型没有返回可用结果。")
            return None

        message = response.choices[0].message
        calls = message.tool_calls
        if not calls:
            print(message.content or message.refusal or "模型没有返回文本。")
            return saw_tool_call if message.content and not message.refusal else None

        if round_number == MAX_ROUNDS:
            print("已达到最大轮数，未生成最终回答。")
            return None

        # 先把模型发出的调用请求加入历史，保留原始 ID 和参数字符串。
        assistant_message = cast(
            ChatCompletionAssistantMessageParam,
            {
                "role": "assistant",
                "content": message.content,
                "tool_calls": [call.model_dump(exclude_none=True) for call in calls],
            },
        )
        messages.append(assistant_message)

        saw_tool_call = True
        for call in calls:
            if call.type == "function":
                print(f"[工具] round={round_number} name={call.function.name!r}")
                content = run_tool_call(call.function.name, call.function.arguments)
            else:
                print(f"[工具] round={round_number} type={call.type!r}")
                content = json.dumps({"error": "Unsupported tool type."})

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": content,
                }
            )

    return None


def main() -> None:
    load_dotenv()
    client = get_chat_client()
    deployment = os.environ["CHAT_DEPLOYMENT"]
    today = datetime.now(ZoneInfo("Pacific/Auckland")).date()

    for question, expected in QUESTIONS:
        print(f"\n问题：{question}", flush=True)
        actual = run_question(client, deployment, today, question)
        mark = "✓" if actual is expected else "✗"
        expected_text = "调用工具" if expected else "直接回答"
        actual_text = {True: "调用工具", False: "直接回答", None: "未完成"}[actual]
        print(f"{mark} 预期：{expected_text} | 实际：{actual_text}")


if __name__ == "__main__":
    main()
