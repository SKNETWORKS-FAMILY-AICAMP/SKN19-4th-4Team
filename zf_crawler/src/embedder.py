"""임베딩 모듈 - OpenAI text-embedding-3-small"""
import os
from typing import List
from langchain_openai import OpenAIEmbeddings

_model = None


def get_model() -> OpenAIEmbeddings:
    """임베딩 모델 싱글톤"""
    global _model
    if _model is None:
        if not os.getenv("OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY 환경변수 필요")
        _model = OpenAIEmbeddings(model="text-embedding-3-small")
    return _model


def embed_text(text: str) -> List[float]:
    """단일 텍스트 임베딩"""
    return get_model().embed_query(text)


def embed_texts(texts: List[str]) -> List[List[float]]:
    """배치 임베딩"""
    return get_model().embed_documents(texts) if texts else []


def embed_chunks(chunks: List) -> List:
    """Chunk 객체 리스트에 임베딩 추가"""
    if not chunks:
        return []
    texts = [c.text for c in chunks]
    for chunk, emb in zip(chunks, embed_texts(texts)):
        chunk.embedding = emb
    return chunks
