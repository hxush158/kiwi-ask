import os
from math import hypot

from dotenv import load_dotenv
from openai import OpenAI

from kiwi_ask.common.llm import get_chat_client


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("向量维度必须相同。")

    norm_a = hypot(*a)
    norm_b = hypot(*b)
    if norm_a == 0 or norm_b == 0:
        raise ValueError("余弦相似度要求两个向量都非零。")

    dot_product = sum(x * y for x, y in zip(a, b, strict=True))
    return dot_product / (norm_a * norm_b)


DOCUMENTS = [
    (
        "Tenancy Services",
        (
            "Residential rent increases in New Zealand generally require "
            "a 12-month interval and advance written notice."
        ),
    ),
    (
        "ACC",
        "A healthcare provider can help lodge an ACC injury claim.",
    ),
    (
        "Natural Hazards Commission",
        "Natural hazards cover may apply to earthquake damage to an insured home.",
    ),
]

QUESTIONS = [
    "My landlord wants more money every few months.",
    "房东每隔几个月就要求我多付钱。",
    # Unrelated on purpose: shows that irrelevant text still scores above 0.
    "What's the best fish and chips in Wellington?",
]

REDUCED_DIMENSIONS = 256


def embed_all(
    client: OpenAI, deployment: str, texts: list[str], dimensions: int | None = None
) -> list[list[float]]:
    """Embed all texts in one request and return vectors in input order."""
    if dimensions is None:
        response = client.embeddings.create(model=deployment, input=texts)
    else:
        response = client.embeddings.create(
            model=deployment, input=texts, dimensions=dimensions
        )

    # index 对应文本在 input 列表中的位置。
    vectors = {item.index: item.embedding for item in response.data}
    if vectors.keys() != set(range(len(texts))):
        raise RuntimeError("返回的向量索引与输入文本不匹配。")

    print(f"维度 {len(vectors[0])}：本批 token 用量 {response.usage.total_tokens}")
    return [vectors[i] for i in range(len(texts))]


def main() -> None:
    load_dotenv()
    client = get_chat_client()
    deployment = os.environ["EMBED_DEPLOYMENT"]

    texts = [text for _, text in DOCUMENTS] + QUESTIONS
    full = embed_all(client, deployment, texts)
    reduced = embed_all(client, deployment, texts, dimensions=REDUCED_DIMENSIONS)

    doc_count = len(DOCUMENTS)
    for offset, question in enumerate(QUESTIONS):
        query = doc_count + offset
        rows = [
            (
                label,
                cosine_similarity(full[query], full[i]),
                cosine_similarity(reduced[query], reduced[i]),
            )
            for i, (label, _) in enumerate(DOCUMENTS)
        ]
        reduced_rank = {
            label: rank
            for rank, (label, _, _) in enumerate(
                sorted(rows, key=lambda row: row[2], reverse=True), start=1
            )
        }

        print(f"\n问题：{question}")
        print(
            f"{'排名':<4} {'文档':<28} {'全维度':>8} "
            f"{REDUCED_DIMENSIONS:>6}维 {REDUCED_DIMENSIONS:>5}维排名"
        )
        for rank, (label, score_full, score_reduced) in enumerate(
            sorted(rows, key=lambda row: row[1], reverse=True), start=1
        ):
            print(
                f"{rank:<6} {label:<28} {score_full:>8.4f} "
                f"{score_reduced:>9.4f} {reduced_rank[label]:>8}"
            )


if __name__ == "__main__":
    main()
