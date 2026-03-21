from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    用户扩展信息模型
    用于存储用户的额外信息，如头像、昵称等
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    # avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    avatar_url = models.URLField(blank=True, null=True, verbose_name='头像URL')
    nickname = models.CharField(max_length=50, blank=True, verbose_name='昵称')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'user_profile'
        verbose_name = '用户信息'
        verbose_name_plural = '用户信息'

    def __str__(self):
        return self.user.username
