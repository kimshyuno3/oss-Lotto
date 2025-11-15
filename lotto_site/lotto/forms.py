from django import forms
from .models import Purchase
from django.core.validators import MinValueValidator, MaxValueValidator

# 로또 번호 유효성 검사기
number_validators = [
    MinValueValidator(1, message="1보다 작은 숫자는 입력할 수 없습니다."),
    MaxValueValidator(45, message="45보다 큰 숫자는 입력할 수 없습니다."),
]

class ManualPurchaseForm(forms.Form):
    """사용자로부터 6개의 수동 로또 번호를 입력받는 폼"""
    # 필드 정의 시 HTML input type을 number로 지정하고, min/max 값 설정
    p_num1 = forms.IntegerField(
        label='번호 1', 
        validators=number_validators, 
        widget=forms.NumberInput(attrs={'min': 1, 'max': 45})
    )
    p_num2 = forms.IntegerField(
        label='번호 2', 
        validators=number_validators, 
        widget=forms.NumberInput(attrs={'min': 1, 'max': 45})
    )
    p_num3 = forms.IntegerField(
        label='번호 3', 
        validators=number_validators, 
        widget=forms.NumberInput(attrs={'min': 1, 'max': 45})
    )
    p_num4 = forms.IntegerField(
        label='번호 4', 
        validators=number_validators, 
        widget=forms.NumberInput(attrs={'min': 1, 'max': 45})
    )
    p_num5 = forms.IntegerField(
        label='번호 5', 
        validators=number_validators, 
        widget=forms.NumberInput(attrs={'min': 1, 'max': 45})
    )
    p_num6 = forms.IntegerField(
        label='번호 6', 
        validators=number_validators, 
        widget=forms.NumberInput(attrs={'min': 1, 'max': 45})
    )

    def clean(self):
        """폼 전체 유효성 검사: 중복된 숫자가 있는지 확인"""
        cleaned_data = super().clean()
        
        # 6개 번호 필드 이름을 리스트로 만듭니다.
        number_fields = ['p_num1', 'p_num2', 'p_num3', 'p_num4', 'p_num5', 'p_num6']
        
        # 모든 번호를 가져와서 집합(set)으로 변환하여 중복을 확인합니다.
        # 값이 유효하지 않아 필드에 데이터가 없으면 NoneType 오류가 발생하므로, 유효한 값만 포함합니다.
        numbers = [cleaned_data.get(f) for f in number_fields if cleaned_data.get(f) is not None]

        if len(numbers) != len(set(numbers)):
            raise forms.ValidationError("로또 번호는 중복될 수 없습니다. 6개의 고유한 숫자를 입력해 주세요.")
            
        return cleaned_data