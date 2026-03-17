"""
URL configuration for zhihui_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from visualization.views import home, about, dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home, name='home'),
    path('about/', about, name='about'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # 用户模块
    path('users/', include('users.urls')),
    
    # 分析模块
    path('analysis/', include('analysis.urls')),
    
    # 可视化模块
    path('visualization/', include('visualization.urls')),
]

# 开发环境下的媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
