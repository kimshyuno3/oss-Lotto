from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone 

# 로또 번호는 1부터 45 사이의 값만 유효하도록 검증합니다.
LOTTO_NUMBER_VALIDATORS = [
    MinValueValidator(1, message="로또 번호는 1보다 작을 수 없습니다."),
    MaxValueValidator(45, message="로또 번호는 45보다 클 수 없습니다.")
]

class LottoRound(models.Model):
    """
    회차별 당첨 번호 정보와 실제 추첨 완료 일시를 저장하는 모델 (관리자 기능)
    """
    round = models.IntegerField(
        unique=True,
        verbose_name="회차",
        help_text="로또 회차 번호"
    )
    # 기존 draw_date(추첨 예정일)을 제거하고, 실제 추첨이 완료된 시점을 기록하는 필드를 추가
    actual_draw_date = models.DateTimeField(
        verbose_name="실제 추첨 일시", 
        null=True, 
        blank=True,
        help_text="관리자가 추첨을 완료한 시점"
    )
    
    # 6개의 당첨 번호: 추첨 전에는 NULL이어야 하므로 null=True, blank=True 추가
    num1 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS, null=True, blank=True)
    num2 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS, null=True, blank=True)
    num3 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS, null=True, blank=True)
    num4 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS, null=True, blank=True)
    num5 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS, null=True, blank=True)
    num6 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS, null=True, blank=True)
    
    # 보너스 번호: 추첨 전에는 NULL이어야 하므로 null=True, blank=True 추가
    bonus_number = models.IntegerField(
        validators=LOTTO_NUMBER_VALIDATORS,
        verbose_name="보너스 번호",
        null=True, 
        blank=True
    )

    def get_winning_numbers(self):
        """당첨 번호 6개를 리스트로 반환 (None이 아닐 경우에만)"""
        if self.num1 is None:
            return []
        return sorted([self.num1, self.num2, self.num3, self.num4, self.num5, self.num6])

    def __str__(self):
        return f"제 {self.round} 회차 (추첨 완료: {self.actual_draw_date.strftime('%Y-%m-%d %H:%M') if self.actual_draw_date else '미완료'})"

class Purchase(models.Model):
    """
    사용자의 로또 구매 기록을 저장하는 모델 (사용자 기능)
    """
    LOTTO_TYPE_CHOICES = [
        ('A', '자동'),
        ('M', '수동'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="구매자")
    # 회차 정보가 삭제되어도 구매 기록을 남기기 위해 on_delete=models.SET_NULL 사용
    round = models.ForeignKey(LottoRound, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="구매 회차")
    
    lotto_type = models.CharField(
        max_length=1, 
        choices=LOTTO_TYPE_CHOICES,
        default='M',
        verbose_name="구매 유형"
    )
    purchase_date = models.DateTimeField(auto_now_add=True, verbose_name="구매 일시")
    
    # 구매한 6개의 번호
    p_num1 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS)
    p_num2 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS)
    p_num3 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS)
    p_num4 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS)
    p_num5 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS)
    p_num6 = models.IntegerField(validators=LOTTO_NUMBER_VALIDATORS)

    def get_purchased_numbers(self):
        """구매한 번호 6개를 리스트로 반환"""
        return sorted([self.p_num1, self.p_num2, self.p_num3, self.p_num4, self.p_num5, self.p_num6])

    def __str__(self):
        return f"{self.user.username}님의 {self.get_purchased_numbers()}"

class SalesPerformance(models.Model):
    """
    회차별 로또 판매 실적을 기록하는 모델 (관리자 기능)
    """
    # round에 OneToOneField를 사용하고 primary_key=True를 설정하여 해당 회차에 실적을 연결
    round = models.OneToOneField(LottoRound, on_delete=models.CASCADE, primary_key=True, verbose_name="회차")
    total_sales = models.IntegerField(default=0, verbose_name="총 판매액 (장)")
    total_winners = models.IntegerField(default=0, verbose_name="총 당첨자 수 (모든 등수)")
    
    # 등수별 당첨자 수
    rank1_winners = models.IntegerField(default=0, verbose_name="1등 당첨자")
    rank2_winners = models.IntegerField(default=0, verbose_name="2등 당첨자")
    rank3_winners = models.IntegerField(default=0, verbose_name="3등 당첨자")
    
    def __str__(self):
        # 사용자 요청 사항 반영
        return f"제 {self.round.round} 회차 판매 실적"