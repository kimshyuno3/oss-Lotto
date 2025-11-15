from django.contrib import admin
from .models import LottoRound, Purchase, SalesPerformance

# LottoRound 모델 등록 및 표시 설정
@admin.register(LottoRound)
class LottoRoundAdmin(admin.ModelAdmin):
    list_display = ('round', 'draw_date', 'get_winning_numbers_display', 'bonus_number')
    search_fields = ('round',)
    list_filter = ('draw_date',)
    ordering = ('-round',)
    
    def get_winning_numbers_display(self, obj):
        return ", ".join(map(str, obj.get_winning_numbers()))
    get_winning_numbers_display.short_description = "당첨 번호"

# Purchase 모델 등록 및 표시 설정
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'round', 'lotto_type', 'purchase_date', 'get_purchased_numbers_display')
    list_filter = ('lotto_type', 'round', 'purchase_date')
    search_fields = ('user__username',)
    ordering = ('-purchase_date',)

    def get_purchased_numbers_display(self, obj):
        return ", ".join(map(str, obj.get_purchased_numbers()))
    get_purchased_numbers_display.short_description = "구매 번호"

# SalesPerformance 모델 등록 및 표시 설정
@admin.register(SalesPerformance)
class SalesPerformanceAdmin(admin.ModelAdmin):
    list_display = ('round', 'total_sales', 'total_winners', 'rank1_winners', 'rank2_winners', 'rank3_winners')
    ordering = ('-round__round',)