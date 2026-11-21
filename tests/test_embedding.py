import pytest

from kiwi_ask.m0_embedding import cosine_similarity


def test_cosine_similarity() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == pytest.approx(1.0)
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)


def test_cosine_similarity_rejects_invalid_vectors() -> None:
    with pytest.raises(ValueError, match="维度"):
        cosine_similarity([1.0], [1.0, 2.0])

    with pytest.raises(ValueError, match="非零"):
        cosine_similarity([0.0], [1.0])
