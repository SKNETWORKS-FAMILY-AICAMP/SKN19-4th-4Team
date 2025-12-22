from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.db.models import Q
import math

from .models import AnncAll, Chat, ChatMessage
from .serializers import (
    AnnouncementListResponseSerializer, AnncSummaryResponseSerializer,
    ChatRequestSerializer, ChatResponseSerializer,
    ChatHistoriesResponseSerializer, ChatHistoryDetailResponseSerializer
)

# ---------------------------------------------------
# 2. 채팅 히스토리 목록 조회 (GET /api/chathistories)
# ---------------------------------------------------
@extend_schema(
    summary="사용자 - 채팅 히스토리 목록 조회",
    operation_id="getChatHistories",
    tags=["채팅 히스토리"],
    parameters=[
        OpenApiParameter(name="user_key", description="사용자 키", required=True, type=str),
    ],
    responses={200: ChatHistoriesResponseSerializer}
)
@api_view(['GET'])
def chat_histories(request):
    """
    사용자의 채팅 히스토리 목록을 조회합니다.
    user_key로 해당 사용자의 모든 채팅 세션을 반환합니다.
    """
    user_key = request.GET.get('user_key', 'anonymous')

    # 실제 DB에서 해당 사용자의 채팅 세션 조회 (최신순)
    chat_sessions = Chat.objects.filter(user_key=user_key).order_by('-updated_at')

    # 응답 데이터 구성
    histories = []
    for chat in chat_sessions:
        histories.append({
            "title": chat.title,
            "session_id": str(chat.session_key)
        })

    response_data = {
        "message": "성공적으로 채팅 히스토리 목록을 조회했습니다.",
        "status": "success",
        "data": histories
    }
    return Response(response_data)

# ---------------------------------------------------
# 3. 특정 채팅 히스토리 상세 조회 (GET /api/chathistories/{session_key})
# ---------------------------------------------------
@extend_schema(
    summary="사용자 - 특정 히스토리 조회",
    operation_id="getChatHistoryDetail",
    tags=["채팅 히스토리"],
    parameters=[
        OpenApiParameter(name="user_key", description="사용자 키", required=True, type=str),
    ],
    responses={200: ChatHistoryDetailResponseSerializer},
    methods=["GET"]
)
@extend_schema(
    summary="사용자 - 채팅 히스토리 삭제",
    operation_id="deleteChatHistory",
    tags=["채팅 히스토리"],
    parameters=[
        OpenApiParameter(name="user_key", description="사용자 키", required=True, type=str),
    ],
    responses={204: None},
    methods=["DELETE"]
)
@api_view(['GET', 'DELETE'])
def chat_history_detail(request, session_key):
    """
    특정 채팅 세션의 상세 대화 내용을 조회합니다.
    session_key로 해당 세션의 모든 메시지를 반환합니다.
    """
    user_key = request.GET.get('user_key', 'anonymous')

    try:
        import uuid
        session_uuid = uuid.UUID(str(session_key))

        chat_session = Chat.objects.filter(
            session_key=session_uuid,
            user_key=user_key
        ).first()

        if not chat_session:
            return Response({
                "message": "해당 채팅 세션을 찾을 수 없습니다.",
                "status": "error",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'DELETE':
            # 메시지 삭제 후 세션 삭제
            ChatMessage.objects.filter(chat=chat_session).delete()
            chat_session.delete()
            return Response({
                "message": "채팅 세션을 삭제했습니다.",
                "status": "success"
            }, status=status.HTTP_200_OK)

        # GET 요청: 세션 메시지 반환
        messages = ChatMessage.objects.filter(chat=chat_session).order_by('sequence')

        chat_list = []
        for msg in messages:
            chat_list.append({
                "id": msg.id,
                "sequence": msg.sequence,
                "message_type": msg.message_type,
                "message": msg.message
            })

        response_data = {
            "message": "성공적으로 특정 채팅 히스토리를 조회했습니다.",
            "status": "success",
            "data": {
                "title": chat_session.title,
                "session_id": str(chat_session.session_key),
                "user_key": chat_session.user_key,
                "chat_list": chat_list
            }
        }
        return Response(response_data)

    except ValueError:
        return Response({
            "message": "유효하지 않은 세션 키 형식입니다.",
            "status": "error",
            "data": None
        }, status=status.HTTP_400_BAD_REQUEST)

# ---------------------------------------------------
# 4. 공고 목록 조회 (GET /api/anncs) - BaseResponse 적용
# ---------------------------------------------------
@extend_schema(
    summary="공고 목록 조회",
    operation_id="getAnnouncementList",
    tags=["공고"],
    parameters=[
        OpenApiParameter(name="annc_title", required=False, type=str),
        OpenApiParameter(name="annc_status", required=False, type=str, enum=["진행중", "마감", "예정"]),
        OpenApiParameter(name="annc_type", required=False, type=str),
        OpenApiParameter(name="items_per_page", required=True, type=int, default=10),
        OpenApiParameter(name="current_page", required=True, type=int, default=1),
    ],
    responses={200: AnnouncementListResponseSerializer}
)
@api_view(['GET'])
def annc_list(request):
    # 1. 파라미터 처리
    annc_title = request.GET.get('annc_title')
    annc_status = request.GET.get('annc_status')
    items_per_page = int(request.GET.get('items_per_page', 10))
    current_page = int(request.GET.get('current_page', 1))

    # 2. 필터링
    queryset = AnncAll.objects.all().filter(service_status='OPEN').order_by('-created_at')
    if annc_title:
        queryset = queryset.filter(annc_title__icontains=annc_title)
    if annc_status:
        queryset = queryset.filter(annc_status=annc_status)

    # 3. 페이징 계산
    total_count = queryset.count()
    total_pages = math.ceil(total_count / items_per_page)
    start = (current_page - 1) * items_per_page
    end = start + items_per_page
    page_data = queryset[start:end]

    # 4. 응답 생성 (BaseResponse 구조 맞춤)
    # 모델 데이터를 직렬화 (AnnouncementItemSerializer 이용)
    # 여기서는 수동으로 구조를 맞춰서 보냅니다.
    from .serializers import AnnouncementItemSerializer
    items_data = AnnouncementItemSerializer(page_data, many=True).data

    response_data = {
        "message": "성공적으로 공고 목록을 조회했습니다.",
        "status": "success",
        "data": {
            "page_info": {
                "total_count": total_count,
                "current_page": current_page,
                "items_per_page": items_per_page,
                "total_pages": total_pages
            },
            "items": items_data
        }
    }
    return Response(response_data)

# ---------------------------------------------------
# 5. 공고 요약 정보 조회 (GET /api/annc_summary)
# ---------------------------------------------------
@extend_schema(
    summary="홈 - 공고 요약 데이터 요약",
    operation_id="getAnnouncementSummary",
    tags=["공고 요약"],
    responses={200: AnncSummaryResponseSerializer}
)
@api_view(['GET'])
def annc_summary(request):
    from datetime import datetime, timedelta
    
    # 실제 DB 집계 로직
    total = AnncAll.objects.count()
    lease = AnncAll.objects.filter(annc_type="임대").count()
    sale = AnncAll.objects.filter(annc_type="분양").count()
    etc = total - (lease + sale)
    
    # 이번 주 신규 공고 계산
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    new_this_week = AnncAll.objects.filter(
        created_at__gte=week_ago,
        created_at__lt=today + timedelta(days=1)
    ).count()

    response_data = {
        "message": "성공적으로 공고 요약 정보를 조회했습니다.",
        "status": "success",
        "data": {
            "cnt_total": total,
            "cnt_lease": lease,
            "cnt_sale": sale,
            "cnt_etc": etc if etc >= 0 else 0,
            "cnt_new_this_week": new_this_week
        }
    }
    return Response(response_data)

class TestApiView(APIView):
    """
    테스트용 REST API View. GET 요청 시 Hello World 메시지를 반환합니다.
    """
    def get(self, request):
        # API 응답으로 보낼 데이터 (JSON 형태로 자동 변환됨)
        data = {
            "message": "Hello, world! (from chatbot REST API)",
            "status": "success"
        }
        return Response(data, status=status.HTTP_200_OK)