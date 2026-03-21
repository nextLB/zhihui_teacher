from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserRegisterForm(UserCreationForm):
    """
    用户注册表单
    继承自Django的UserCreationForm，添加邮箱字段
    """
    email = forms.EmailField(
        required=True,
        label='邮箱',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': '请输入邮箱地址'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入用户名'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super(UserRegisterForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '请输入密码'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': '请再次输入密码'
        })
    
    def save(self, commit=True):
        user = super(UserRegisterForm, self).save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            UserProfile.objects.create(user=user)
        return user


class UserProfileForm(forms.ModelForm):
    """
    用户资料表单
    用于编辑用户个人资料
    """
    class Meta:
        model = UserProfile
        fields = ('nickname', 'phone', 'avatar_url')
        widgets = {
            'nickname': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入昵称'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入电话号码'
            }),
            'avatar_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': '请输入头像URL'
            }),
        }
