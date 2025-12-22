# chatbot/services.py
"""
Django ORM 기반 서비스 레이어
- AnncAllRepository -> AnncAllService
- DocChunkRepository -> DocChunkService
"""

import re
from typing import List, Dict, Any, Optional
from django.db.models import Q, F
from django.db import connection
from .models import AnncAll, DocChunks, AnncFiles, Chat, ChatMessage


# 한국어 조사 제거 패턴
PARTICLES = re.compile(
    r'(은|는|이|가|을|를|의|에|에서|로|으로|와|과|도|만|까지|부터|에게|한테|께|보다|처럼|같이|마다|밖에|라도|조차|야|이야|이나|나|든지|건|란|라는|이라는)$'
)


def strip_particles(text: str) -> str:
    """한국어 조사를 제거하여 검색 정확도 향상"""
    words = text.split()
    return ' '.join(PARTICLES.sub('', w) for w in words)


class AnncAllService:
    """공고 관련 서비스"""

    @staticmethod
    def search_announcements(
        annc_status: Optional[List[str]] = None,
        annc_type: Optional[str] = None,
        annc_region: Optional[str] = None,
        keyword: Optional[str] = None,
        service_status: str = 'OPEN',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        조건 기반 공고 검색 (RDB)

        :param annc_status: 공고 상태 필터 ['접수중', '공고중'] 등
        :param annc_type: 공고 유형 필터 (임대, 분양 등 - LIKE 검색)
        :param annc_region: 지역 필터 (서울, 경기 등 - LIKE 검색)
        :param keyword: 제목 키워드 검색 (LIKE 검색)
        :param service_status: 서비스 상태 (기본 'OPEN')
        :param limit: 최대 반환 개수
        :return: 공고 목록
        """
        queryset = AnncAll.objects.filter(service_status=service_status)

        # 공고 상태 필터
        if annc_status:
            # 문자열이면 리스트로 변환
            if isinstance(annc_status, str):
                annc_status = [annc_status]
            queryset = queryset.filter(annc_status__in=annc_status)

        # 공고 유형 필터 (LIKE 검색)
        if annc_type:
            queryset = queryset.filter(annc_type__icontains=annc_type)

        # 지역 필터 (LIKE 검색)
        if annc_region:
            queryset = queryset.filter(annc_region__icontains=annc_region)

        # 키워드 검색 (제목)
        if keyword:
            queryset = queryset.filter(annc_title__icontains=keyword)

        # 정렬 및 제한
        queryset = queryset.order_by('-annc_pblsh_dt')[:limit]

        # Dict 변환
        return list(queryset.values(
            'annc_id', 'annc_title', 'annc_url', 'corp_cd', 'annc_type',
            'annc_dtl_type', 'annc_region', 'annc_pblsh_dt',
            'annc_deadline_dt', 'annc_status', 'service_status'
        ))

    @staticmethod
    def get_announcement_by_id(annc_id: int) -> Optional[Dict[str, Any]]:
        """공고 ID로 단일 공고 조회"""
        try:
            annc = AnncAll.objects.filter(annc_id=annc_id).values(
                'annc_id', 'annc_title', 'annc_url', 'corp_cd', 'annc_type',
                'annc_dtl_type', 'annc_region', 'annc_pblsh_dt',
                'annc_deadline_dt', 'annc_status', 'service_status'
            ).first()
            return annc
        except AnncAll.DoesNotExist:
            return None

    @staticmethod
    def get_announcements_by_ids(annc_ids: List[int]) -> List[Dict[str, Any]]:
        """여러 공고 ID로 공고 목록 조회"""
        if not annc_ids:
            return []

        return list(AnncAll.objects.filter(annc_id__in=annc_ids).values(
            'annc_id', 'annc_title', 'annc_url', 'corp_cd', 'annc_type',
            'annc_dtl_type', 'annc_region', 'annc_pblsh_dt',
            'annc_deadline_dt', 'annc_status', 'service_status'
        ).order_by('annc_id'))


class DocChunkService:
    """문서 청크 관련 서비스"""

    @staticmethod
    def search_by_vector_similarity(
        query_vector: List[float],
        limit: int = 5,
        annc_id_filter: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        쿼리 벡터와 가장 유사한 청크를 L2 distance로 검색
        """
        # annc_id 필터 조건
        if annc_id_filter:
            annc_filter = f"AND annc_id IN ({','.join(map(str, annc_id_filter))})"
        else:
            annc_filter = ""

        query = f"""
            SELECT chunk_id, chunk_text, chunk_type, page_num,
                   annc_id, file_id, embedding <-> %s::vector AS distance
            FROM doc_chunks
            WHERE embedding IS NOT NULL {annc_filter}
            ORDER BY distance
            LIMIT %s
        """

        with connection.cursor() as cursor:
            cursor.execute(query, [query_vector, limit])
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return results

    @staticmethod
    def hybrid_search(
        query_text: str,
        query_embedding: List[float],
        top_k: int = 10,
        fts_weight: float = 0.4,
        vec_weight: float = 0.6,
        rrf_k: int = 60,
        annc_id_filter: Optional[List[int]] = None
    ) -> List[Dict[str, Any]]:
        """
        FTS와 벡터 검색을 결합한 하이브리드 검색 (RRF 리랭킹).

        :param query_text: 검색 쿼리 텍스트
        :param query_embedding: 쿼리 임베딩 벡터
        :param top_k: 반환할 결과 수
        :param fts_weight: FTS 점수 가중치
        :param vec_weight: 벡터 유사도 가중치
        :param rrf_k: RRF 상수 (기본 60)
        :param annc_id_filter: 특정 공고 ID만 검색 (None이면 전체 검색)
        :return: 검색 결과 리스트
        """
        # 한국어 조사 제거 후 FTS 쿼리 생성
        processed_query = strip_particles(query_text)
        words = processed_query.split()
        # 1글자 이상인 단어만 포함
        fts_terms = [w for w in words if len(w) >= 1]
        if not fts_terms:
            fts_terms = words

        # OR 조건으로 FTS 쿼리 (한 단어라도 매칭되면 검색)
        fts_query = ' | '.join(fts_terms)

        # annc_id 필터 조건 생성
        if annc_id_filter:
            annc_ids_str = ','.join(map(str, annc_id_filter))
            annc_filter_fts = f"AND annc_id IN ({annc_ids_str})"
            annc_filter_vec = f"AND annc_id IN ({annc_ids_str})"
        else:
            annc_filter_fts = ""
            annc_filter_vec = ""

        query = f"""
            WITH fts_results AS (
                SELECT chunk_id,
                       ts_rank(fts_vector, to_tsquery('simple', %s)) AS fts_score,
                       ROW_NUMBER() OVER (ORDER BY ts_rank(fts_vector, to_tsquery('simple', %s)) DESC) AS fts_rank
                FROM doc_chunks
                WHERE fts_vector @@ to_tsquery('simple', %s) {annc_filter_fts}
            ),
            vec_results AS (
                SELECT chunk_id,
                       1 - (embedding <=> %s::vector) AS vec_score,
                       ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS vec_rank
                FROM doc_chunks
                WHERE embedding IS NOT NULL {annc_filter_vec}
                LIMIT 100
            ),
            combined AS (
                SELECT COALESCE(f.chunk_id, v.chunk_id) AS chunk_id,
                       COALESCE(f.fts_score, 0) AS fts_score,
                       COALESCE(v.vec_score, 0) AS vec_score,
                       COALESCE(f.fts_rank, 1000) AS fts_rank,
                       COALESCE(v.vec_rank, 1000) AS vec_rank
                FROM fts_results f
                FULL OUTER JOIN vec_results v ON f.chunk_id = v.chunk_id
            )
            SELECT c.chunk_id,
                   d.chunk_text,
                   d.chunk_type,
                   d.page_num,
                   d.annc_id,
                   d.file_id,
                   c.fts_score,
                   c.vec_score,
                   (%s / (c.fts_rank + %s) + %s / (c.vec_rank + %s)) AS rrf_score
            FROM combined c
            JOIN doc_chunks d ON c.chunk_id = d.chunk_id
            ORDER BY rrf_score DESC
            LIMIT %s
        """

        params = [
            fts_query, fts_query, fts_query,
            query_embedding, query_embedding,
            fts_weight, rrf_k, vec_weight, rrf_k,
            top_k
        ]

        with connection.cursor() as cursor:
            cursor.execute(query, params)
            columns = [col[0] for col in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return results


class ChatHistoryService:
    """채팅 기록 관련 서비스 (Chat + ChatMessage 모델 사용)"""

    @staticmethod
    def get_or_create_chat(session_key: str, user_key: str = "anonymous") -> Chat:
        """세션 키로 Chat 조회 또는 생성"""
        import uuid

        try:
            # UUID로 변환 시도
            session_uuid = uuid.UUID(session_key)
        except ValueError:
            # UUID 형식이 아니면 새로 생성
            session_uuid = uuid.uuid4()

        chat, created = Chat.objects.get_or_create(
            session_key=session_uuid,
            defaults={'user_key': user_key, 'title': '새로운 채팅'}
        )
        return chat

    @staticmethod
    def get_history_by_session(session_key: str, limit: int = 20) -> List[Dict[str, Any]]:
        """세션별 채팅 기록 조회"""
        import uuid

        try:
            session_uuid = uuid.UUID(session_key)
        except ValueError:
            return []

        try:
            chat = Chat.objects.get(session_key=session_uuid)
        except Chat.DoesNotExist:
            return []

        return list(ChatMessage.objects.filter(
            chat=chat
        ).order_by('sequence')[:limit].values(
            'id', 'sequence', 'message', 'message_type', 'created_at'
        ))

    @staticmethod
    def add_message(
        session_key: str,
        message: str,
        message_type: str,
        user_key: str = "anonymous"
    ) -> ChatMessage:
        """채팅 메시지 추가"""
        # Chat 가져오거나 생성
        chat = ChatHistoryService.get_or_create_chat(session_key, user_key)

        # 현재 세션의 마지막 sequence 조회
        last_msg = ChatMessage.objects.filter(
            chat=chat
        ).order_by('-sequence').first()

        next_sequence = (last_msg.sequence + 1) if last_msg else 1

        return ChatMessage.objects.create(
            chat=chat,
            sequence=next_sequence,
            message=message,
            message_type=message_type
        )

    @staticmethod
    def get_recent_messages(session_key: str, count: int = 10) -> List[Dict[str, str]]:
        """최근 메시지를 LangGraph 형식으로 반환"""
        import uuid

        try:
            session_uuid = uuid.UUID(session_key)
        except ValueError:
            return []

        try:
            chat = Chat.objects.get(session_key=session_uuid)
        except Chat.DoesNotExist:
            return []

        messages = ChatMessage.objects.filter(
            chat=chat
        ).order_by('-sequence')[:count]

        # 역순으로 반환 (오래된 것부터)
        result = []
        for msg in reversed(messages):
            role = 'assistant' if msg.message_type == 'bot' else msg.message_type
            result.append({
                'role': role,
                'content': msg.message
            })
        return result
