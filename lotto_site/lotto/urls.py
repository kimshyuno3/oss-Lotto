from django.urls import path
from . import views

urlpatterns = [
    # --------------------------------------------------------
    # 사용자 기능
    # --------------------------------------------------------
    # 메인 페이지
    path('', views.lotto_home, name='lotto_home'), 
    # 로또 구매 페이지
    path('purchase/', views.lotto_purchase, name='lotto_purchase'),
    # 당첨 확인 페이지
    path('winnings/', views.check_winnings, name='check_winnings'),
    path('signup/', views.SignUpView.as_view(), name='signup'),
    # --------------------------------------------------------
    # 관리자 기능 (로또 시스템 흐름을 따름)
    # --------------------------------------------------------
    # 관리자 대시보드 메인
    path('admin_panel/', views.admin_dashboard, name='admin_dashboard'),
    
    # 1. 다음 회차 생성 (판매 시작)
    # 뷰 이름: create_next_round로 변경됨 (이전의 draw_lotto_round 대체)
    path('admin_panel/create_next_round/', views.create_next_round, name='create_next_round'), 
    
    # 2. 현재 회차 추첨 및 마감 (당첨 번호 확정)
    # 뷰 이름: finalize_lotto_round 신규 추가
    path('admin_panel/finalize_round/', views.finalize_lotto_round, name='finalize_lotto_round'), 
    
]