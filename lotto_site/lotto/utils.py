# lotto/utils.py

def determine_lotto_rank(purchased_numbers, winning_numbers, bonus_number):
    """
    구매 번호와 당첨 번호를 비교하여 당첨 등수를 판정하는 함수.
    
    :param purchased_numbers: 구매자가 선택한 6개의 번호 (정렬된 리스트)
    :param winning_numbers: 당첨 번호 6개 (정렬된 리스트)
    :param bonus_number: 보너스 번호 1개 (정수)
    :return: 당첨 등수 (1, 2, 3, 4, 5) 또는 0 (낙첨)
    """
    
    # 1. 일치하는 메인 번호 개수 확인
    match_count = len(set(purchased_numbers) & set(winning_numbers))
    
    # 2. 보너스 번호 일치 여부 확인 (2등 판별용)
    has_bonus = bonus_number in purchased_numbers

    if match_count == 6:
        # 6개 일치 (보너스 번호 상관없음)
        return 1  # 1등
    elif match_count == 5:
        if has_bonus:
            return 2  # 2등 (5개 일치 + 보너스 일치)
        else:
            return 3  # 3등 (5개 일치 + 보너스 불일치)
    elif match_count == 4:
        return 4  # 4등 (4개 일치)
    elif match_count == 3:
        return 5  # 5등 (3개 일치)
    else:
        return 0  # 낙첨