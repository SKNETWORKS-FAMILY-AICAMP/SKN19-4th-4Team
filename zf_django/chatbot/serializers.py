from rest_framework import serializers
from .models import AnncAll  # 공고 모델은 있다고 가정

# 이 파일은 input, output에서의 언어 변환의 자동화 및 데이터 검증을 위해 만들어졌습니다.

# ==========================================
# 1. 공통 응답 래퍼 (BaseResponse 패턴 구현)
# ==========================================
class BaseResponseSerializer(serializers.Serializer):
    message = serializers.CharField(default="요청을 성공적으로 처리했습니다.")
    status = serializers.CharField(default="success")
    # data 필드는 상속받는 클래스에서 구체적으로 정의

# ==========================================
# 2. 공고(Announcement) 관련 시리얼라이저
# ==========================================
class AnnouncementItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnncAll
        fields = [
            'annc_id', 'annc_title', 'annc_url', 'created_at', 'annc_status', 'annc_type', 'annc_dtl_type', 'annc_region', 'annc_pblsh_dt', 'annc_deadline_dt'
        ]

class PageInfoSerializer(serializers.Serializer):
    total_count = serializers.IntegerField()
    current_page = serializers.IntegerField()
    items_per_page = serializers.IntegerField()
    total_pages = serializers.IntegerField()

class AnnouncementDataSerializer(serializers.Serializer):
    page_info = PageInfoSerializer()
    items = AnnouncementItemSerializer(many=True)

class AnnouncementListResponseSerializer(BaseResponseSerializer):
    data = AnnouncementDataSerializer()

# 공고 요약
class AnncSummaryDataSerializer(serializers.Serializer):
    cnt_total = serializers.IntegerField()
    cnt_lease = serializers.IntegerField()
    cnt_sale = serializers.IntegerField()
    cnt_etc = serializers.IntegerField()
    cnt_new_this_week = serializers.IntegerField()

class AnncSummaryResponseSerializer(BaseResponseSerializer):
    data = AnncSummaryDataSerializer()

# ==========================================
# 3. 채팅(Chat) 관련 시리얼라이저
# ==========================================
class ChatMessageSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    sequence = serializers.IntegerField()
    message_type = serializers.CharField()  # system, user, bot
    message = serializers.CharField()

class ChatRequestSerializer(serializers.Serializer):
    user_key = serializers.CharField()
    session_id = serializers.CharField()
    user_message = serializers.CharField()

class ChatResponseDataSerializer(serializers.Serializer):
    ai_response = ChatMessageSerializer()

class ChatResponseSerializer(BaseResponseSerializer):
    data = ChatResponseDataSerializer()

# 채팅 히스토리 목록
class ChatShortSerializer(serializers.Serializer):
    title = serializers.CharField()
    session_id = serializers.CharField()

class ChatHistoriesResponseSerializer(BaseResponseSerializer):
    data = ChatShortSerializer(many=True)

# 채팅 히스토리 상세
class ChatHistoryDetailDataSerializer(serializers.Serializer):
    title = serializers.CharField()
    session_id = serializers.CharField()
    user_key = serializers.CharField()
    chat_list = ChatMessageSerializer(many=True)

class ChatHistoryDetailResponseSerializer(BaseResponseSerializer):
    data = ChatHistoryDetailDataSerializer()