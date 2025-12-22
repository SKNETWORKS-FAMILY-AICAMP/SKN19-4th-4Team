# web/urls.py
from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('main/', views.main_view, name='main'),
    path('user-info/', views.user_info_view, name='user_info'),
    path('user-info-modify/', views.user_info_modify_view, name='user_info_modify'),
    path('chat/', views.chat_view, name='chat'),
    path('list/', views.list_view, name='list'),
    # 기존 URL 유지 (하위 호환성)
    path('chat-interface/', views.chat_interface, name='chat_interface'),
]