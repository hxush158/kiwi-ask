import os
import time

from dotenv import load_dotenv
from kiwi_ask.common.llm import get_chat_client


EFFORTS = ["minimal", "low", "medium", "high"]

QUESTIONS = [
    "用一句话解释什么是 embedding。",
    "我在奥克兰租房，房东 8 个月前涨过租金，现在又通知要涨，合法吗？",
]

def main():
    load_dotenv()

    # 关闭自动重试，避免把重试耗时混进正常请求的结果。
    client = get_chat_client().with_options(
        max_retries=0,
        timeout=120.0,
    )
    deployment = os.environ["CHAT_DEPLOYMENT"]
    for question in QUESTIONS:
        print(f"\n{'=' * 60}")
        print(f"问题：{question}")

        for effort in EFFORTS:
            print(f"\n正在测试 {effort} ...", flush=True)
            start = time.perf_counter()

            response = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": question}],
                reasoning_effort=effort,
            )

            elapsed = time.perf_counter() - start
            usage = response.usage
            choice = response.choices[0]

            if usage is not None:
                details = usage.completion_tokens_details
                reasoning = (
                    details.reasoning_tokens
                    if details is not None
                    else None
                )
                visible = (
                    usage.completion_tokens - reasoning
                    if reasoning is not None
                    else None
                )

                print(
                    f"effort={effort} | "
                    f"input={usage.prompt_tokens} | "
                    f"reasoning={reasoning} | "
                    f"visible={visible} | "
                    f"completion={usage.completion_tokens} | "
                    f"time={elapsed:.2f}s"
                )
            else:
                print(f"未返回用量数据 | time={elapsed:.2f}s")

            print(f"finish_reason={choice.finish_reason}")
            print("回答：")
            print(choice.message.content or "[没有文本回答]")


if __name__ == "__main__":
    main()