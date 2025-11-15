from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth.decorators import login_required, user_passes_test # <-- 이 부분을 추가합니다.
from django.contrib import messages
from django.db.models import Prefetch
from django.contrib.auth.mixins import UserPassesTestMixin # UserPassesTestMixin 유지
from django.utils import timezone
from django.http import HttpResponse
from datetime import date, timedelta
import random
from django.urls import reverse_lazy # redirect 경로를 지연 로드하기 위해 필요
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm # 기본 회원가입 폼 사용

# 로또 앱 내에서 정의된 모델과 폼, 유틸리티 함수를 import합니다.
from .models import Purchase, LottoRound, SalesPerformance 
from .forms import ManualPurchaseForm
from .utils import determine_lotto_rank 

# ----------------------------------------------------------------------
# 헬퍼 함수
# ----------------------------------------------------------------------

def get_current_round():
    """
    현재 시점에서 구매 가능한 (가장 최근의) 로또 회차를 반환합니다.
    (당첨 번호가 아직 확정되지 않은 회차 중 가장 높은 회차)
    """
    try:
        # num1이 null (추첨 번호가 정해지지 않음)인 회차 중 가장 높은 회차를 찾습니다.
        current_round = LottoRound.objects.filter(num1__isnull=True).latest('round')
    except LottoRound.DoesNotExist:
        # 구매 가능한 회차가 없으면 None 반환
        return None
    
    return current_round

def generate_auto_numbers():
    """1부터 45 사이의 중복 없는 랜덤한 6개 번호를 생성하고 정렬하여 반환합니다."""
    return sorted(random.sample(range(1, 46), 6))

def generate_winning_numbers():
    """당첨 번호 6개와 보너스 번호 1개를 생성하는 헬퍼 함수"""
    all_numbers = list(range(1, 46))
    winning_numbers = random.sample(all_numbers, 6)
    
    # 보너스 번호는 당첨 번호에 포함되지 않은 수 중에서 선택
    remaining_numbers = [n for n in all_numbers if n not in winning_numbers]
    # remaining_numbers가 비어있지 않다고 가정하고 choice를 사용 (1~45 중 6개 선택이므로 항상 39개 이상 남음)
    bonus_number = random.choice(remaining_numbers)
    
    return sorted(winning_numbers), bonus_number

# ----------------------------------------------------------------------
# 사용자 기능 뷰
# ----------------------------------------------------------------------

class SignUpView(CreateView):
    form_class = UserCreationForm  # Django가 제공하는 기본 폼 사용
    # 회원가입 성공 후 리다이렉트할 URL (lazy를 사용하여 URL 로딩 순서 문제 방지)
    # 여기서는 로그인 페이지로 리다이렉트하도록 설정합니다.
    success_url = reverse_lazy('login') 
    template_name = 'registration/signup.html'
def lotto_home(request):
    """메인 페이지 뷰 (로그인 상태에 따라 메시지 변경)"""
    if request.user.is_authenticated:
        message = f"안녕하세요, {request.user.username}님! 로또 구매를 시작하려면 메뉴를 이용하세요."
    else:
        message = '로또 서비스를 이용하려면 로그인해 주세요.'
    
    return render(request, 'lotto/index.html', {
        'message': message,
    }) 

@login_required
def lotto_purchase(request):
    """로또 구매 (수동/자동) 처리 뷰입니다."""
    
    current_round = get_current_round()
    
    # 1. 구매 가능한 회차 확인
    if not current_round:
        messages.error(request, "현재 구매 가능한 로또 회차가 없습니다. 관리자에게 문의하세요.")
        return redirect('lotto_home') 

    if request.method == 'POST':
        # 2. 수동 구매 처리
        if 'manual_purchase' in request.POST:
            form = ManualPurchaseForm(request.POST)
            if form.is_valid():
                # 번호를 오름차순으로 정렬하여 저장합니다.
                sorted_numbers = sorted([
                    form.cleaned_data['p_num1'], form.cleaned_data['p_num2'], form.cleaned_data['p_num3'],
                    form.cleaned_data['p_num4'], form.cleaned_data['p_num5'], form.cleaned_data['p_num6']
                ])

                Purchase.objects.create(
                    user=request.user,
                    round=current_round,
                    lotto_type='M', # Manual
                    p_num1=sorted_numbers[0], p_num2=sorted_numbers[1], p_num3=sorted_numbers[2],
                    p_num4=sorted_numbers[3], p_num5=sorted_numbers[4], p_num6=sorted_numbers[5],
                )
                messages.success(request, f"로또 (수동) 구매가 완료되었습니다. 번호: {sorted_numbers}")
                return redirect('lotto_purchase') # 중복 제출 방지
            
        # 3. 자동 구매 처리
        elif 'auto_purchase' in request.POST:
            # 6개의 랜덤 번호를 생성합니다.
            auto_numbers = generate_auto_numbers() 
            
            Purchase.objects.create(
                user=request.user,
                round=current_round,
                lotto_type='A', # Auto
                p_num1=auto_numbers[0], p_num2=auto_numbers[1], p_num3=auto_numbers[2],
                p_num4=auto_numbers[3], p_num5=auto_numbers[4], p_num6=auto_numbers[5],
            )
            messages.success(request, f"로또 (자동) 구매가 완료되었습니다. 번호: {auto_numbers}")
            return redirect('lotto_purchase') 

    # 4. GET 요청 (페이지 표시)
    else:
        form = ManualPurchaseForm()
    
    context = {
        'form': form,
        'current_round': current_round,
    }
    return render(request, 'lotto/purchase.html', context)


@login_required
def check_winnings(request):
    """사용자의 전체 구매 내역을 조회하고 당첨 결과를 판정하는 뷰입니다."""
    
    # 구매 기록과 해당 회차 정보를 한 번의 쿼리로 가져옵니다.
    purchases = Purchase.objects.filter(user=request.user).select_related('round').order_by('-purchase_date')

    results = []
    
    for purchase in purchases:
        purchased_numbers = purchase.get_purchased_numbers() 
        winning_numbers = []
        bonus_number = None
        rank = -1 # 초기값: -1 (추첨 대기 중)

        if purchase.round:
            # LottoRound가 존재하고, 당첨 번호가 확정된 경우에만 판정 시도
            if purchase.round.num1 is not None:
                try:
                    winning_round = purchase.round
                    winning_numbers = winning_round.get_winning_numbers()
                    bonus_number = winning_round.bonus_number
                    
                    # 3. 당첨 판정 로직 실행
                    rank = determine_lotto_rank(purchased_numbers, winning_numbers, bonus_number)
                    
                except AttributeError:
                    rank = -2 # 오류 상태 (회차 정보는 있지만 번호 가져오기 오류)
        
        results.append({
            'purchase': purchase,
            'purchased_numbers': purchased_numbers,
            'winning_numbers': winning_numbers,
            'bonus_number': bonus_number,
            'rank': rank,
        })
        
    context = {
        'results': results,
    }
    return render(request, 'lotto/winnings.html', context)

# ----------------------------------------------------------------------
# 관리자 기능 뷰
# ----------------------------------------------------------------------

# 1. 관리자 대시보드 (View)
@user_passes_test(lambda u: u.is_superuser)
@login_required
def admin_dashboard(request):
    """관리자 전용 대시보드 뷰: 최근 회차 정보 및 전체 실적 목록 제공"""
    
    # 별도로 is_superuser를 체크할 필요 없이 데코레이터가 처리합니다.
    # 단, 데코레이터가 실패할 경우 기본 리다이렉트가 'accounts/login'이 될 수 있으므로, 
    # 필요한 경우 settings.py에 LOGIN_URL이나 LOGIN_REDIRECT_URL을 설정해야 합니다.

    # 1. 가장 최근 생성된 회차 정보
    try:
        latest_round = LottoRound.objects.latest('round')
        # 다음 회차 번호 계산
        next_round_number = latest_round.round + 1
    except LottoRound.DoesNotExist:
        latest_round = None
        next_round_number = 1
        
    # 2. **[추가]** 모든 판매 실적 목록을 최신 회차(내림차순)로 가져옵니다.
    # SalesPerformance는 LottoRound와 OneToOne 관계이므로, select_related('round')로 LottoRound 정보를 효율적으로 가져옵니다.
    all_sales_performance = SalesPerformance.objects.select_related('round').order_by('-round__round')

    context = {
        'latest_round': latest_round,
        'next_round_number': next_round_number,
        # **[추가]** 전체 실적 목록
        'all_sales_performance': all_sales_performance, 
    }
    
    return render(request, 'lotto/admin_dashboard.html', context)

# 2. 다음 회차 생성 (판매 시작) 뷰
@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_next_round(request):
    """
    다음 회차를 생성합니다. (당첨 번호는 비워두고 판매를 시작함)
    URL 이름이 draw_lotto_round에서 create_next_round로 변경됨.
    """
    if request.method == 'POST':
        try:
            latest_round = LottoRound.objects.latest('round')
            next_round_number = latest_round.round + 1
            # 이전 회차 추첨일로부터 일주일 후로 설정 (단순화)
            next_draw_date = latest_round.draw_date + timedelta(days=7) 
        except LottoRound.DoesNotExist:
            # 최초 회차 생성 (1회차)
            next_round_number = 1
            next_draw_date = date.today() + timedelta(days=7)
        
        # 새로운 회차를 당첨 번호 없이 생성
        LottoRound.objects.create(
            round=next_round_number,
            draw_date=next_draw_date
        )
        
        messages.success(request, f"**제 {next_round_number} 회차**가 성공적으로 생성되었으며, 지금부터 구매 가능합니다.")
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')

@user_passes_test(lambda u: u.is_superuser)
@login_required
def finalize_lotto_round(request):
    if request.method == 'POST':
        try:
            # 1. 추첨 대상 회차 찾기 (가장 최근에 생성되었지만, 아직 당첨 번호가 없는 회차)
            current_round = LottoRound.objects.filter(num1__isnull=True).order_by('-round').first()
            if not current_round:
                messages.error(request, "현재 추첨을 진행할 로또 회차가 없습니다. 먼저 다음 회차를 생성해 주세요.")
                return redirect('admin_dashboard')
            
            round_number = current_round.round
            
            # 2. 당첨 번호 생성 및 LottoRound에 저장 (추첨 및 마감)
            all_numbers = list(range(1, 46))
            # 7개의 번호를 동시에 뽑아 6개는 당첨, 1개는 보너스로 사용
            winning_set = set(random.sample(all_numbers, 7)) 
            
            winning_numbers = sorted(list(winning_set)[:6])
            bonus_number = list(winning_set - set(winning_numbers))[0]
            
            current_round.num1, current_round.num2, current_round.num3 = winning_numbers[0], winning_numbers[1], winning_numbers[2]
            current_round.num4, current_round.num5, current_round.num6 = winning_numbers[3], winning_numbers[4], winning_numbers[5]
            current_round.bonus_number = bonus_number
            current_round.save()
            
            # --------------------------------------------------------
            # 3. 실적 및 당첨자 집계 (자동 실행)
            # --------------------------------------------------------
            
            all_purchases = Purchase.objects.filter(round=current_round)
            total_sales = all_purchases.count()
            
            rank_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            total_winners = 0

            for purchase in all_purchases:
                purchased_numbers = purchase.get_purchased_numbers()
                
                # utils.py의 당첨 판정 로직 사용
                rank = determine_lotto_rank(purchased_numbers, winning_numbers, bonus_number)
                
                if rank > 0:
                    if rank in rank_counts:
                        rank_counts[rank] += 1
                    total_winners += 1
                    
            # 4. SalesPerformance 모델에 저장
            SalesPerformance.objects.create(
                round=current_round,
                total_sales=total_sales,
                total_winners=total_winners,
                rank1_winners=rank_counts[1],
                rank2_winners=rank_counts[2],
                rank3_winners=rank_counts[3],
            )

            # 5. 메시지 및 리다이렉션
            messages.success(request, 
                f"✅ **제 {round_number} 회차** 추첨 및 판매 실적 집계가 완료되었습니다! "
                f"이제 다음 회차를 생성하여 판매를 시작해 주세요."
            )
            return redirect('admin_dashboard')
            
        except Exception as e:
            messages.error(request, f"추첨 및 실적 집계 중 오류가 발생했습니다: {e}")
            return redirect('admin_dashboard')
            
    return redirect('admin_dashboard') # GET 요청 처리