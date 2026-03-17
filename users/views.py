from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import UserRegisterForm, UserProfileForm
from .models import UserProfile


class UserLoginView(LoginView):
    """
    用户登录视图
    处理用户登录操作
    """
    template_name = 'users/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('home')
    
    def form_invalid(self, form):
        messages.error(self.request, '用户名或密码错误')
        return super().form_invalid(form)


class UserRegisterView(CreateView):
    """
    用户注册视图
    处理用户注册操作
    """
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '注册成功！请登录。')
        return response


class UserLogoutView(LogoutView):
    """
    用户登出视图
    """
    next_page = 'home'


@login_required
def profile_view(request):
    """
    用户资料页面视图
    显示和编辑用户个人资料
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染用户资料页面
    """
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, '资料更新成功！')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=user_profile)
    
    return render(request, 'users/profile.html', {
        'form': form,
        'user_profile': user_profile
    })


def user_login(request):
    """
    用户登录视图 (函数式)
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, '用户名或密码错误')
    return render(request, 'users/login.html')


def user_register(request):
    """
    用户注册视图 (函数式)
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象
    """
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '注册成功！')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def user_logout(request):
    """
    用户登出视图 (函数式)
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 重定向到首页
    """
    logout(request)
    return redirect('home')
