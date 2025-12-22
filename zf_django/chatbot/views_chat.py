from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q
import math
import uuid
import json
import logging

from .models import AnncAll, Chat, ChatMessage
from .serializers import (
    AnnouncementListResponseSerializer, AnncSummaryResponseSerializer,
    ChatRequestSerializer, ChatResponseSerializer,
    ChatHistoriesResponseSerializer, ChatHistoryDetailResponseSerializer
)
from .graph import chat as langgraph_chat

logger = logging.getLogger(__name__)


# ---------------------------------------------------
# Helper: 사용자 프로필 추출
# ---------------------------------------------------
def _extract_user_profile(data: dict) -> dict:
    """
    API 요청 데이터에서 사용자 프로필 정보를 추출합니다.

    Args:
        data: request.data 딕셔너리

    Returns:
        user_profile 딕셔너리 (값이 있는 필드만 포함)
    """
    profile_fields = [
        'ref_hope_area',   # 희망 지역 (str)
        'ref_age',         # 연령 (int)
        'ref_marriged',    # 혼인 여부 (str, 'Y'/'N')
        'ref_children',    # 자녀 수 (int)
        'ref_income',      # 연소득 만원 (int)
    ]

    user_profile = {}
    for field in profile_fields:
        value = data.get(field)
        if value is not None and value != '':
            user_profile[field] = value

    return user_profile if user_profile else None


# ---------------------------------------------------
# Helper: announcement_id로 공고 조회 및 selected_annc 형식 변환
# ---------------------------------------------------
def _get_announcement_by_id(announcement_id: str) -> dict:
    """
    announcement_id로 공고를 조회하여 selected_annc 형식으로 반환합니다.

    Args:
        announcement_id: 공고 ID (annc_id)

    Returns:
        공고 딕셔너리 (selected_annc 형식) 또는 None
    """
    if not announcement_id:
        return None

    try:
        annc = AnncAll.objects.get(annc_id=announcement_id)
        return {
            'annc_id': annc.annc_id,
            'annc_title': annc.annc_title,
            'annc_type': annc.annc_type,
            'annc_dtl_type': annc.annc_dtl_type,
            'annc_region': annc.annc_region,
            'annc_status': annc.annc_status,
            'annc_pblsh_dt': annc.annc_pblsh_dt,
            'annc_deadline_dt': annc.annc_deadline_dt,
            'annc_url': annc.annc_url,
            'corp_cd': annc.corp_cd,
        }
    except AnncAll.DoesNotExist:
        logger.warning(f"Announcement not found: {announcement_id}")
        return None


# ---------------------------------------------------
# Helper: 세션 상태 복원 (마지막 bot 메시지의 prompt에서)
# ---------------------------------------------------
def _restore_session_state(chat_session) -> dict:
    """
    마지막 bot 메시지의 prompt 필드에서 세션 상태를 복원합니다.

    Args:
        chat_session: Chat 모델 인스턴스

    Returns:
        복원된 세션 상태 딕셔너리 (prev_anncs, selected_annc, search_history)
    """
    default_state = {
        'search_history': [],
        'prev_anncs': [],
        'selected_annc': None,
        'selected_anncs': []  # 비교용 다중 선택 공고
    }

    if not chat_session:
        return default_state

    # 마지막 bot 메시지 조회
    last_bot_msg = ChatMessage.objects.filter(
        chat=chat_session,
        message_type='bot'
    ).order_by('-sequence').first()

    if not last_bot_msg or not last_bot_msg.prompt:
        return default_state

    try:
        # prompt 필드에서 JSON 파싱
        saved_state = json.loads(last_bot_msg.prompt)
        return {
            'search_history': saved_state.get('search_history', []),
            'prev_anncs': saved_state.get('prev_anncs', []),
            'selected_annc': saved_state.get('selected_annc'),
            'selected_anncs': saved_state.get('selected_anncs', [])  # 비교용 다중 선택 공고
        }
    except (json.JSONDecodeError, TypeError):
        return default_state


# ---------------------------------------------------
# 1. 채팅 메시지 등록 및 AI 응답 (POST /api/chat)
# ---------------------------------------------------
@extend_schema(
    summary="사용자 - 신규 채팅 메시지 등록 및 AI 응답 받기",
    operation_id="postChatMessage",
    tags=["채팅"],
    request=ChatRequestSerializer,
    responses={200: ChatResponseSerializer}
)
@api_view(['POST'])
def chat_message(request):
    """
    사용자 메시지를 받아 LangGraph 기반 챗봇으로 AI 응답을 생성합니다.
    """
    user_msg = request.data.get('user_message', '')
    session_id = request.data.get('session_id')
    user_key = request.data.get('user_key', 'anonymous')
    announcement_id = request.data.get('announcement_id')  # 공고 컨텍스트 모드

    if not user_msg:
        return Response({
            "message": "user_message는 필수입니다.",
            "status": "error",
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 세션 처리: 기존 세션 조회 또는 새 세션 생성
        if session_id:
            try:
                session_uuid = uuid.UUID(session_id)
                chat_session = Chat.objects.filter(session_key=session_uuid).first()
            except ValueError:
                chat_session = None
        else:
            chat_session = None

        # 새 세션 생성
        if not chat_session:
            session_uuid = uuid.uuid4()
            chat_session = Chat.objects.create(
                session_key=session_uuid,
                user_key=user_key,
                title=user_msg[:50] if len(user_msg) > 50 else user_msg
            )

        # 이전 대화 히스토리 로드 (session_state 구성)
        previous_messages = ChatMessage.objects.filter(
            chat=chat_session
        ).order_by('sequence')

        chat_history = []
        for msg in previous_messages:
            role = 'user' if msg.message_type == 'user' else 'assistant'
            chat_history.append({'role': role, 'content': msg.message})

        # 사용자 프로필 추출 (API 요청에서)
        user_profile = _extract_user_profile(request.data)

        # 이전 세션 상태 복원 (prev_anncs, selected_annc, search_history)
        restored_state = _restore_session_state(chat_session)

        # announcement_id가 있으면 해당 공고를 컨텍스트로 설정
        # (기존 selected_annc와 다른 공고인 경우에도 새 공고로 교체)
        if announcement_id:
            current_annc_id = restored_state['selected_annc'].get('annc_id') if restored_state['selected_annc'] else None
            if str(current_annc_id) != str(announcement_id):
                annc_data = _get_announcement_by_id(announcement_id)
                if annc_data:
                    restored_state['selected_annc'] = annc_data
                    restored_state['prev_anncs'] = [annc_data]
                    restored_state['search_history'] = []  # 새 공고 컨텍스트이므로 검색 히스토리 초기화
                    logger.info(f"Announcement context set: {annc_data.get('annc_title')}")

        # 세션 상태 구성
        session_state = {
            'chat_history': chat_history,
            'search_history': restored_state['search_history'],
            'prev_anncs': restored_state['prev_anncs'],
            'selected_annc': restored_state['selected_annc'],
            'selected_anncs': restored_state['selected_anncs'],  # 비교용 다중 선택 공고
            'user_profile': user_profile
        }

        # LangGraph 챗봇 호출
        result = langgraph_chat(user_msg, session_state)
        ai_response = result.get('answer', '응답을 생성하지 못했습니다.')

        # 결과에서 업데이트된 세션 상태 추출
        updated_session_state = result.get('session_state', {})
        state_to_save = {
            'search_history': updated_session_state.get('search_history', []),
            'prev_anncs': updated_session_state.get('prev_anncs', []),
            'selected_annc': updated_session_state.get('selected_annc'),
            'selected_anncs': updated_session_state.get('selected_anncs', [])  # 비교용 다중 선택 공고
        }

        # 현재 최대 sequence 조회
        last_seq = ChatMessage.objects.filter(chat=chat_session).order_by('-sequence').first()
        next_seq = (last_seq.sequence + 1) if last_seq else 1

        # 사용자 메시지 저장
        ChatMessage.objects.create(
            chat=chat_session,
            sequence=next_seq,
            message=user_msg,
            prompt=user_msg,
            message_type='user'
        )

        # AI 응답 저장 (prompt 필드에 세션 상태 JSON 저장)
        bot_message = ChatMessage.objects.create(
            chat=chat_session,
            sequence=next_seq + 1,
            message=ai_response,
            prompt=json.dumps(state_to_save, ensure_ascii=False),
            message_type='bot'
        )

        response_data = {
            "message": "성공적으로 메시지를 등록하고 AI 응답을 받았습니다.",
            "status": "success",
            "data": {
                "ai_response": {
                    "id": bot_message.id,
                    "session_id": str(chat_session.session_key),
                    "sequence": bot_message.sequence,
                    "message_type": "bot",
                    "message": ai_response
                }
            }
        }
        return Response(response_data)

    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return Response({
            "message": f"채팅 처리 중 오류가 발생했습니다: {str(e)}",
            "status": "error",
            "data": None
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)