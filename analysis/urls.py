from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    # 音频相关
    path('audio/upload/', views.upload_audio, name='upload_audio'),
    path('audio/list/', views.audio_list, name='audio_list'),
    path('audio/<int:audio_id>/', views.audio_detail, name='audio_detail'),
    path('audio/<int:audio_id>/analyze/', views.start_audio_analysis, name='start_audio_analysis'),
    path('audio/<int:audio_id>/progress/', views.audio_analysis_progress, name='audio_analysis_progress'),
    path('audio/<int:audio_id>/delete/', views.delete_audio, name='delete_audio'),
    
    # 视频相关
    path('video/upload/', views.upload_video, name='upload_video'),
    path('video/list/', views.video_list, name='video_list'),
    path('video/<int:video_id>/', views.video_detail, name='video_detail'),
    path('video/<int:video_id>/analyze/', views.start_video_analysis, name='start_video_analysis'),
    path('video/<int:video_id>/progress/', views.video_analysis_progress, name='video_analysis_progress'),
    path('video/<int:video_id>/delete/', views.delete_video, name='delete_video'),
    
    # 数据采集
    path('data/collection/', views.data_collection, name='data_collection'),
    path('data/save/', views.save_collection, name='save_collection'),
    
    # 风格画像
    path('profile/create/', views.create_profile, name='create_profile'),
    path('profile/list/', views.profile_list, name='profile_list'),
    path('profile/<int:profile_id>/', views.profile_detail, name='profile_detail'),
    path('profile/<int:profile_id>/generate/', views.generate_profile_image, name='generate_profile_image'),
    path('profile/<int:profile_id>/delete/', views.delete_profile, name='delete_profile'),
]
