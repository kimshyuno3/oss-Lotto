from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('', include('lotto.urls')), # lotto 앱의 URL 포함
    # 인증 관련 URL도 추가해야 합니다 (로그인/로그아웃). 예시:
]