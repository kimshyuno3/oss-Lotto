from django.contrib import admin
from .models import LottoRound, Purchase, SalesPerformance

# 1. utils.py 파일에서 당첨 판별 함수 가져오기
from lotto.utils import determine_lotto_rank 

# --- LottoRound 모델 ---
@admin.register(LottoRound)
class LottoRoundAdmin(admin.ModelAdmin):
    list_display = ('round', 'actual_draw_date', 'get_winning_numbers_display', 'bonus_number')
    search_fields = ('round',)
    list_filter = ('actual_draw_date',)
    ordering = ('-round',)
    
    def get_winning_numbers_display(self, obj):
        # obj.get_winning_numbers()는 모델에 정의된 당첨 번호 반환 메서드 사용
        return ", ".join(map(str, obj.get_winning_numbers()))
    get_winning_numbers_display.short_description = "당첨 번호"

# --- Purchase 모델 (핵심 수정 부분) ---
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    # list_display에 'user'와 'get_winning_rank_display' 유지
    list_display = (
        'id', 
        'user', 
        'round', 
        'lotto_type', 
        'get_purchased_numbers_display',
        'get_winning_rank_display', # 관리자 페이지에 당첨 등수 표시
        'purchase_date',
    )
    
    list_filter = ('lotto_type', 'round', 'purchase_date')
    search_fields = ('user__username', 'round__round') # 사용자 이름 및 회차 번호 검색
    ordering = ('-purchase_date',)

    def get_purchased_numbers_display(self, obj):
        """구매 번호를 보기 쉽게 표시"""
        return ", ".join(map(str, obj.get_purchased_numbers()))
    get_purchased_numbers_display.short_description = "구매 번호"

    def get_winning_rank_display(self, obj):
        """
        [핵심 로직] determine_lotto_rank 함수를 사용하여 당첨 등수를 계산하고 반환합니다.
        """
        # 1. 해당 구매 회차의 당첨 번호 정보(LottoRound)가 존재하는지 확인
        if obj.round and obj.round.num1 and obj.round.bonus_number:
            # 당첨 번호 리스트 (6개)
            winning_numbers = obj.round.get_winning_numbers()
            # 보너스 번호
            bonus_number = obj.round.bonus_number
            # 구매 번호 리스트 (6개)
            purchased_numbers = obj.get_purchased_numbers()
            
            # 2. 당첨 등수 판별 함수 호출
            rank = determine_lotto_rank(purchased_numbers, winning_numbers, bonus_number)
            
            # 3. 등수에 따라 표시할 문자열 반환
            if rank == 0:
                return "낙첨 (0)"
            elif 1 <= rank <= 5:
                return f"✅ {rank}등 당첨"
            else:
                return "오류"
        
        # 당첨 번호 정보가 아직 입력되지 않은 경우
        return "추첨 전"

    get_winning_rank_display.short_description = "당첨 등수"

# --- SalesPerformance 모델 ---
@admin.register(SalesPerformance)
class SalesPerformanceAdmin(admin.ModelAdmin):
    list_display = ('round', 'total_sales', 'total_winners', 'rank1_winners', 'rank2_winners', 'rank3_winners')
    ordering = ('-round__round',)