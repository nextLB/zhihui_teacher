from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from analysis.models import AudioFile, VideoFile, TeacherStyleProfile, AudioAnalysisResult, VideoAnalysisResult


def home(request):
    """
    首页视图
    展示系统概览和快速入口
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染首页
    """
    context = {
        'title': '智慧课堂教师语音特征可视化与风格画像系统'
    }
    
    if request.user.is_authenticated:
        # 获取用户统计数据
        context['audio_count'] = AudioFile.objects.filter(user=request.user).count()
        context['video_count'] = VideoFile.objects.filter(user=request.user).count()
        context['profile_count'] = TeacherStyleProfile.objects.filter(user=request.user).count()
        context['recent_audios'] = AudioFile.objects.filter(user=request.user).order_by('-upload_time')[:5]
        context['recent_videos'] = VideoFile.objects.filter(user=request.user).order_by('-upload_time')[:5]
        context['recent_profiles'] = TeacherStyleProfile.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    return render(request, 'visualization/home.html', context)


def about(request):
    """
    关于页面视图
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染关于页面
    """
    return render(request, 'visualization/about.html')


@login_required
def dashboard(request):
    """
    用户仪表盘视图
    展示用户上传的文件和画像统计
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染仪表盘页面
    """
    audios = AudioFile.objects.filter(user=request.user)
    videos = VideoFile.objects.filter(user=request.user)
    profiles = TeacherStyleProfile.objects.filter(user=request.user)
    
    # 统计数据
    completed_audios = audios.filter(status='completed').count()
    completed_videos = videos.filter(status='completed').count()
    completed_profiles = profiles.count()
    
    context = {
        'total_audios': audios.count(),
        'completed_audios': completed_audios,
        'total_videos': videos.count(),
        'completed_videos': completed_videos,
        'total_profiles': completed_profiles,
        'recent_audios': audios.order_by('-upload_time')[:5],
        'recent_videos': videos.order_by('-upload_time')[:5],
        'recent_profiles': profiles.order_by('-created_at')[:3]
    }
    
    return render(request, 'visualization/dashboard.html', context)


@login_required
def radar_chart(request, profile_id):
    """
    雷达图数据API视图
    
    参数:
        request: HttpRequest对象
        profile_id: int - 风格画像ID
        
    返回:
        JsonResponse - 雷达图数据
    """
    profile = get_object_or_404(TeacherStyleProfile, id=profile_id, user=request.user)
    radar_data = profile.radar_data
    
    return JsonResponse(radar_data)


@login_required
def timeline_chart(request, profile_id):
    """
    时序图数据API视图
    
    参数:
        request: HttpRequest对象
        profile_id: int - 风格画像ID
        
    返回:
        JsonResponse - 时序图数据
    """
    profile = get_object_or_404(TeacherStyleProfile, id=profile_id, user=request.user)
    timeline_data = profile.timeline_data
    
    return JsonResponse(timeline_data)


@login_required
def tone_distribution(request, audio_id):
    """
    语气分布饼图数据API视图
    
    参数:
        request: HttpRequest对象
        audio_id: int - 音频文件ID
        
    返回:
        JsonResponse - 饼图数据
    """
    audio = get_object_or_404(AudioFile, id=audio_id, user=request.user)
    
    if audio.status != 'completed':
        return JsonResponse({'error': '音频分析未完成'}, status=400)
    
    result = audio.analysis_result
    
    # 语气分布数据
    tone_distribution = {
        'encouraging': 0.25,  # 鼓励型
        'guiding': 0.25,      # 引导型
        'lecture': 0.25,     # 讲授型
        'neutral': 0.25      # 中性型
    }
    
    # 根据实际分析结果调整
    tone_type = result.tone_type
    if tone_type == '鼓励型':
        tone_distribution['encouraging'] = result.tone_confidence
    elif tone_type == '引导型':
        tone_distribution['guiding'] = result.tone_confidence
    elif tone_type == '讲授型':
        tone_distribution['lecture'] = result.tone_confidence
    else:
        tone_distribution['neutral'] = result.tone_confidence
    
    # 归一化
    total = sum(tone_distribution.values())
    if total > 0:
        tone_distribution = {k: v/total for k, v in tone_distribution.items()}
    
    return JsonResponse(tone_distribution)


@login_required
def question_types_chart(request, audio_id):
    """
    提问类型分布图数据API视图
    
    参数:
        request: HttpRequest对象
        audio_id: int - 音频文件ID
        
    返回:
        JsonResponse - 提问类型数据
    """
    audio = get_object_or_404(AudioFile, id=audio_id, user=request.user)
    
    if audio.status != 'completed':
        return JsonResponse({'error': '音频分析未完成'}, status=400)
    
    result = audio.analysis_result
    question_types = result.question_types
    
    return JsonResponse(question_types)


@login_required
def student_behavior_chart(request, video_id):
    """
    学生行为统计图数据API视图
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        JsonResponse - 学生行为数据
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    
    if video.status != 'completed':
        return JsonResponse({'error': '视频分析未完成'}, status=400)
    
    result = video.analysis_result
    
    behavior_data = {
        'hand_raising': result.student_hand_raising_count,
        'standing': result.student_standing_count,
        'head_down': result.student_head_down_count
    }
    
    return JsonResponse(behavior_data)


@login_required
def posture_timeline(request, video_id):
    """
    教师姿态时序图数据API视图
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        JsonResponse - 姿态时序数据
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    
    if video.status != 'completed':
        return JsonResponse({'error': '视频分析未完成'}, status=400)
    
    result = video.analysis_result
    posture_timeline = result.teacher_posture_timeline
    
    return JsonResponse({'timeline': posture_timeline})
