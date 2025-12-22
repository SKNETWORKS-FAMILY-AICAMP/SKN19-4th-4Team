# web/views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# -------------------
# 랜딩 페이지
# -------------------
def landing_view(request):
    return render(request, "web/landing.html")

# -------------------
# 메인 페이지 (대시보드)
# -------------------
def main_view(request):
    return render(request, "web/main.html")

# -------------------
# 사용자 정보 입력 페이지
# -------------------
def user_info_view(request):
    # 사용자 정보는 프론트엔드에서 관리 (API 호출 시 전달)
    # Django session에 저장하지 않음
    return render(request, "web/user_info.html")

# -------------------
# 사용자 정보 수정 페이지
# -------------------
def user_info_modify_view(request):
    # 사용자 정보 수정 페이지
    return render(request, "web/user_info_modify.html")

# -------------------
# 채팅 페이지
# -------------------
def chat_view(request):
    # user_key, session_id는 프론트엔드에서 관리
    # API 호출 시 프론트엔드에서 전달
    return render(request, "web/chat.html")

# -------------------
# 공고 목록 페이지
# -------------------
def list_view(request):
    return render(request, "web/list.html")

# 기존 함수 유지 (하위 호환성)
def index(request):
    return landing_view(request)

def chat_interface(request):
    """
    채팅 인터페이스 페이지를 렌더링합니다.
    """
    return chat_view(request)