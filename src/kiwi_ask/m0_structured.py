import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from kiwi_ask.common.llm import get_chat_client

Agency = Literal["Tenancy Services", "ACC", "Natural Hazards Commission", "Other"]


class Enquiry(BaseModel):
    # Field descriptions are sent to the model as part of the JSON schema,
    # so they work as instructions for each field.
    agency: Agency = Field(
        description=(
            "The single primary agency to contact. Use 'Other' when none of "
            "Tenancy Services, ACC or Natural Hazards Commission is responsible."
        )
    )
    topic: str = Field(description="Short English label, e.g. 'rent increase'.")
    urgency: Literal["low", "medium", "high"] = Field(
        description=(
            "high = safety risk or a deadline within days; "
            "medium = needs action within weeks; "
            "low = general information request."
        )
    )
    summary: str = Field(
        description="One-sentence summary in Chinese that keeps every request."
    )


# (question, expected primary agency)
CASES: list[tuple[str, Agency]] = [
    (
        "我在奥克兰租房，房东一直没修漏水的屋顶，我该找谁咨询？",
        "Tenancy Services",
    ),
    ("我在工地摔伤了腰，想了解怎么申请工伤理赔。", "ACC"),
    (
        "地震后我家外墙出现裂缝，想了解怎么申报房屋损坏。",
        "Natural Hazards Commission",
    ),
    (
        (
            "地震后我家外墙出现裂缝，我也在撤离时摔伤了。"
            "我想了解房屋损坏和受伤分别怎么理赔。"
        ),
        # Two agencies apply; one field can only hold one. Watch the summary.
        "Natural Hazards Commission",
    ),
    ("我的个人所得税退税怎么申请？", "Other"),
]


def main() -> None:
    load_dotenv()
    client = get_chat_client()
    deployment = os.environ["CHAT_DEPLOYMENT"]
    passed = 0

    for question, expected in CASES:
        print(f"\n问题：{question}", flush=True)

        response = client.chat.completions.parse(
            model=deployment,
            reasoning_effort="low",
            response_format=Enquiry,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你负责给新西兰的咨询分流。"
                        "每条咨询选择一个主要机构。"
                        "如果涉及多个诉求，在中文摘要里保留所有诉求。"
                    ),
                },
                {"role": "user", "content": question},
            ],
        )

        if not response.choices:
            print("模型没有返回可用结果。")
            continue

        message = response.choices[0].message
        enquiry = message.parsed

        if enquiry is not None:
            ok = enquiry.agency == expected
            passed += ok
            mark = "✓" if ok else "✗"
            print(f"{mark} 分流机构：{enquiry.agency}（预期：{expected}）")
            print(enquiry.model_dump_json(indent=2))
        elif message.refusal:
            print(f"模型拒绝回答：{message.refusal}")
        else:
            print("模型没有返回可解析的分类结果。")

    print(f"\n结果：{passed}/{len(CASES)} 与预期一致")


if __name__ == "__main__":
    main()
