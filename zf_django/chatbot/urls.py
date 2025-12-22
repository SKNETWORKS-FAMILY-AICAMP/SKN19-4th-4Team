from django.urls import path
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from chatbot.views_chat import chat_message  # 추후 합칠때 없애야 함

urlpatterns = [
    # API 문서화
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('test/', views.TestApiView.as_view(), name='test_api'),
    
    # 채팅
    path('chat', chat_message, name='chat-message'),
    path('chathistories', views.chat_histories, name='chat-histories'),
    path('chathistories/<uuid:session_key>', views.chat_history_detail, name='chat-history-detail'),
    
    # 공고
    path('anncs', views.annc_list, name='annc-list'),
    path('annc_summary', views.annc_summary, name='annc-summary'),

    
]