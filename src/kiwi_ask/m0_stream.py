import os
import time

from dotenv import load_dotenv
from openai.types.shared import ReasoningEffort

from kiwi_ask.common.llm import get_chat_client

EFFORTS: list[ReasoningEffort] = ["minimal", "low", "medium", "high"]

QUESTIONS = [
    "给第一次去 Devonport 的游客推荐一个半日行程。",
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

            first_text_at: float | None = None
            usage = None
            started_at = time.perf_counter()

            stream = client.chat.completions.create(
                model=deployment,
                messages=[{"role": "user", "content": question}],
                reasoning_effort=effort,
                stream=True,
                stream_options={"include_usage": True},
            )

            for chunk in stream:
                if chunk.usage is not None:
                    usage = chunk.usage

                if not chunk.choices:
                    continue

                text = chunk.choices[0].delta.content
                if not text:
                    continue

                if first_text_at is None:
                    first_text_at = time.perf_counter()

                print(text, end="", flush=True)

            finished_at = time.perf_counter()

            print()
            if first_text_at is not None:
                print(f"First visible text: {first_text_at - started_at:.3f} s")
            else:
                print("First visible text: N/A")

            print(f"Total stream time:  {finished_at - started_at:.3f} s")

            if usage is not None:
                print(
                    f"Tokens: input={usage.prompt_tokens}, "
                    f"output={usage.completion_tokens}, "
                    f"total={usage.total_tokens}"
                )
            else:
                print("Tokens: N/A")


if __name__ == "__main__":
    main()
