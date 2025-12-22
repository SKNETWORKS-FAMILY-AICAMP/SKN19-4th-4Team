"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

# 각 app으로 라우팅 기능만 한다.
urlpatterns = [
    # path('admin/', admin.site.urls),
    # 웹 페이지 (랜딩 페이지 포함) - 먼저 매칭되도록 먼저 배치
    path('', include('web.urls')),
    # API 엔드포인트 - web.urls 이후에 매칭 (루트 경로가 아닌 API 경로만)
    path('api/', include('chatbot.urls')),
]
