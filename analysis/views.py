from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings
import os
import threading

from .models import AudioFile, VideoFile, AudioAnalysisResult, VideoAnalysisResult, TeacherStyleProfile
from .audio_processor import analyze_audio
from .video_processor import analyze_video
from .profile_builder import build_style_profile


@login_required
def upload_audio(request):
    """
    上传音频文件视图
    处理用户上传课堂音频文件
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象
    """
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        audio_file = request.FILES.get('audio_file')
        
        if not audio_file:
            messages.error(request, '请选择音频文件')
            return redirect('upload_audio')
        
        # 获取文件扩展名
        file_ext = audio_file.name.split('.')[-1].lower() if '.' in audio_file.name else 'other'
        if file_ext not in ['mp3', 'wav', 'm4a']:
            messages.error(request, '不支持的文件格式，请上传MP3、WAV或M4A文件')
            return redirect('upload_audio')
        
        # 创建音频文件记录
        audio = AudioFile.objects.create(
            user=request.user,
            title=title or audio_file.name,
            description=description,
            file=audio_file,
            file_type=file_ext,
            file_size=audio_file.size,
            status='pending'
        )
        
        messages.success(request, '音频文件上传成功！')
        return redirect('audio_detail', audio_id=audio.id)
    
    return render(request, 'analysis/upload_audio.html')


@login_required
def upload_video(request):
    """
    上传视频文件视图
    处理用户上传课堂视频文件
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象
    """
    if request.method == 'POST':
        title = request.POST.get('title', '')
        description = request.POST.get('description', '')
        video_file = request.FILES.get('video_file')
        
        if not video_file:
            messages.error(request, '请选择视频文件')
            return redirect('upload_video')
        
        # 获取文件扩展名
        file_ext = video_file.name.split('.')[-1].lower() if '.' in video_file.name else 'other'
        if file_ext not in ['mp4', 'avi', 'mov']:
            messages.error(request, '不支持的文件格式，请上传MP4、AVI或MOV文件')
            return redirect('upload_video')
        
        # 创建视频文件记录
        video = VideoFile.objects.create(
            user=request.user,
            title=title or video_file.name,
            description=description,
            file=video_file,
            file_type=file_ext,
            file_size=video_file.size,
            status='pending'
        )
        
        messages.success(request, '视频文件上传成功！')
        return redirect('video_detail', video_id=video.id)
    
    return render(request, 'analysis/upload_video.html')


@login_required
def audio_list(request):
    """
    音频文件列表视图
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染音频列表页面
    """
    audios = AudioFile.objects.filter(user=request.user).order_by('-upload_time')
    paginator = Paginator(audios, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'analysis/audio_list.html', {
        'page_obj': page_obj,
        'audios': audios
    })


@login_required
def video_list(request):
    """
    视频文件列表视图
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染视频列表页面
    """
    videos = VideoFile.objects.filter(user=request.user).order_by('-upload_time')
    paginator = Paginator(videos, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'analysis/video_list.html', {
        'page_obj': page_obj,
        'videos': videos
    })


@login_required
def audio_detail(request, audio_id):
    """
    音频详情视图
    
    参数:
        request: HttpRequest对象
        audio_id: int - 音频文件ID
        
    返回:
        HttpResponse对象 - 渲染音频详情页面
    """
    audio = get_object_or_404(AudioFile, id=audio_id, user=request.user)
    analysis_result = None
    
    if audio.status == 'completed':
        try:
            analysis_result = audio.analysis_result
        except AudioAnalysisResult.DoesNotExist:
            pass
    
    return render(request, 'analysis/audio_detail.html', {
        'audio': audio,
        'analysis_result': analysis_result
    })


@login_required
def video_detail(request, video_id):
    """
    视频详情视图
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        HttpResponse对象 - 渲染视频详情页面
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    analysis_result = None
    
    if video.status == 'completed':
        try:
            analysis_result = video.analysis_result
        except VideoAnalysisResult.DoesNotExist:
            pass
    
    return render(request, 'analysis/video_detail.html', {
        'video': video,
        'analysis_result': analysis_result
    })


def run_audio_analysis(audio_id):
    """
    后台运行音频分析任务的函数
    
    参数:
        audio_id: int - 音频文件ID
    """
    try:
        audio = AudioFile.objects.get(id=audio_id)
        audio.status = 'processing'
        audio.save()
        
        # 调用音频分析算法
        # 注意: 这里调用的是analysis/audio_processor.py中定义的分析函数
        # 用户需要在那些函数中实现具体的算法代码
        result = analyze_audio(audio.file.path)
        
        # 保存分析结果
        AudioAnalysisResult.objects.create(
            audio_file=audio,
            speech_rate=result.get('speech_rate', 0),
            pitch_frequency=result.get('pitch_frequency', 0),
            short_time_energy=result.get('short_time_energy', 0),
            mfcc=result.get('mfcc', {}),
            tone_type=result.get('tone_type', '中性型'),
            tone_confidence=result.get('tone_confidence', 0),
            transcribed_text=result.get('transcribed_text', ''),
            question_types=result.get('question_types', {}),
            utterance_length_avg=result.get('utterance_length_avg', 0),
            valid_speech_duration=result.get('valid_speech_duration', 0),
            silence_duration=result.get('silence_duration', 0)
        )
        
        audio.status = 'completed'
        audio.processed_time = timezone.now()
        audio.save()
        
    except Exception as e:
        audio = AudioFile.objects.get(id=audio_id)
        audio.status = 'failed'
        audio.save()
        print(f"音频分析错误: {str(e)}")


def run_video_analysis(video_id):
    """
    后台运行视频分析任务的函数
    
    参数:
        video_id: int - 视频文件ID
    """
    try:
        video = VideoFile.objects.get(id=video_id)
        video.status = 'processing'
        video.save()
        
        # 调用视频分析算法
        # 注意: 这里调用的是analysis/video_processor.py中定义的分析函数
        # 用户需要在那些函数中实现具体的算法代码
        result = analyze_video(video.file.path)
        
        # 保存分析结果
        VideoAnalysisResult.objects.create(
            video_file=video,
            teacher_standing_ratio=result.get('teacher_standing_ratio', 0),
            teacher_walking_ratio=result.get('teacher_walking_ratio', 0),
            teacher_writing_ratio=result.get('teacher_writing_ratio', 0),
            teacher_facing_students_ratio=result.get('teacher_facing_students_ratio', 0),
            teacher_posture_timeline=result.get('teacher_posture_timeline', []),
            student_hand_raising_count=result.get('student_hand_raising_count', 0),
            student_standing_count=result.get('student_standing_count', 0),
            student_head_down_count=result.get('student_head_down_count', 0),
            student_behavior_timeline=result.get('student_behavior_timeline', []),
            interaction_count=result.get('interaction_count', 0),
            teacher_movement_range=result.get('teacher_movement_range', 0),
            student_attention_ratio=result.get('student_attention_ratio', 0),
            key_frames=result.get('key_frames', [])
        )
        
        video.status = 'completed'
        video.processed_time = timezone.now()
        video.save()
        
    except Exception as e:
        video = VideoFile.objects.get(id=video_id)
        video.status = 'failed'
        video.save()
        print(f"视频分析错误: {str(e)}")


@login_required
def start_audio_analysis(request, audio_id):
    """
    启动音频分析任务视图
    
    参数:
        request: HttpRequest对象
        audio_id: int - 音频文件ID
        
    返回:
        HttpResponse对象 - 重定向到音频详情页
    """
    audio = get_object_or_404(AudioFile, id=audio_id, user=request.user)
    
    if audio.status != 'pending':
        messages.warning(request, '该文件已经在处理中或已完成')
        return redirect('audio_detail', audio_id=audio.id)
    
    # 启动后台分析任务
    thread = threading.Thread(target=run_audio_analysis, args=(audio_id,))
    thread.start()
    
    messages.success(request, '音频分析任务已启动，请稍后刷新页面查看结果')
    return redirect('audio_detail', audio_id=audio.id)


@login_required
def start_video_analysis(request, video_id):
    """
    启动视频分析任务视图
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        HttpResponse对象 - 重定向到视频详情页
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    
    if video.status != 'pending':
        messages.warning(request, '该文件已经在处理中或已完成')
        return redirect('video_detail', video_id=video.id)
    
    # 启动后台分析任务
    thread = threading.Thread(target=run_video_analysis, args=(video_id,))
    thread.start()
    
    messages.success(request, '视频分析任务已启动，请稍后刷新页面查看结果')
    return redirect('video_detail', video_id=video.id)


@login_required
def create_profile(request):
    """
    创建风格画像视图
    根据已分析的音频和视频创建综合风格画像
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象
    """
    if request.method == 'POST':
        name = request.POST.get('name', '')
        audio_id = request.POST.get('audio_id')
        video_id = request.POST.get('video_id')
        
        if not audio_id and not video_id:
            messages.error(request, '请至少选择一个已分析的音频或视频')
            return redirect('create_profile')
        
        audio_result = None
        video_result = None
        
        if audio_id:
            audio = get_object_or_404(AudioFile, id=audio_id, user=request.user, status='completed')
            audio_result = audio.analysis_result
        
        if video_id:
            video = get_object_or_404(VideoFile, id=video_id, user=request.user, status='completed')
            video_result = video.analysis_result
        
        # 构建风格画像
        audio_features = {}
        video_features = {}
        
        if audio_result:
            audio_features = {
                'speech_rate': audio_result.speech_rate,
                'tone_type': audio_result.tone_type,
                'question_types': audio_result.question_types,
                'utterance_length_avg': audio_result.utterance_length_avg
            }
        
        if video_result:
            video_features = {
                'teacher_standing_ratio': video_result.teacher_standing_ratio,
                'teacher_walking_ratio': video_result.teacher_walking_ratio,
                'teacher_writing_ratio': video_result.teacher_writing_ratio,
                'teacher_facing_students_ratio': video_result.teacher_facing_students_ratio,
                'student_hand_raising_count': video_result.student_hand_raising_count,
                'interaction_count': video_result.interaction_count
            }
        
        # 调用风格画像构建函数
        profile_data = build_style_profile(audio_features, video_features)
        
        # 保存画像
        profile = TeacherStyleProfile.objects.create(
            user=request.user,
            name=name or f"{request.user.username}的风格画像",
            audio_result=audio_result,
            video_result=video_result,
            style_type=profile_data.get('style_type', 'mixed'),
            style_tags=profile_data.get('style_tags', []),
            feature_vector=profile_data.get('feature_vector', {}),
            radar_data=profile_data.get('radar_data', {}),
            timeline_data=profile_data.get('timeline_data', {})
        )
        
        messages.success(request, '风格画像创建成功！')
        return redirect('profile_detail', profile_id=profile.id)
    
    # 获取用户已完成的音频和视频
    completed_audios = AudioFile.objects.filter(user=request.user, status='completed')
    completed_videos = VideoFile.objects.filter(user=request.user, status='completed')
    
    return render(request, 'analysis/create_profile.html', {
        'completed_audios': completed_audios,
        'completed_videos': completed_videos
    })


@login_required
def profile_list(request):
    """
    风格画像列表视图
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染画像列表页面
    """
    profiles = TeacherStyleProfile.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(profiles, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'analysis/profile_list.html', {
        'page_obj': page_obj,
        'profiles': profiles
    })


@login_required
def profile_detail(request, profile_id):
    """
    风格画像详情视图
    
    参数:
        request: HttpRequest对象
        profile_id: int - 画像ID
        
    返回:
        HttpResponse对象 - 渲染画像详情页面
    """
    profile = get_object_or_404(TeacherStyleProfile, id=profile_id, user=request.user)
    
    return render(request, 'analysis/profile_detail.html', {
        'profile': profile
    })


@login_required
def delete_audio(request, audio_id):
    """
    删除音频文件视图
    
    参数:
        request: HttpRequest对象
        audio_id: int - 音频文件ID
        
    返回:
        HttpResponse对象 - 重定向到音频列表
    """
    audio = get_object_or_404(AudioFile, id=audio_id, user=request.user)
    audio.file.delete()
    audio.delete()
    messages.success(request, '音频文件已删除')
    return redirect('audio_list')


@login_required
def delete_video(request, video_id):
    """
    删除视频文件视图
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        HttpResponse对象 - 重定向到视频列表
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    video.file.delete()
    video.delete()
    messages.success(request, '视频文件已删除')
    return redirect('video_list')


@login_required
def delete_profile(request, profile_id):
    """
    删除风格画像视图
    
    参数:
        request: HttpRequest对象
        profile_id: int - 画像ID
        
    返回:
        HttpResponse对象 - 重定向到画像列表
    """
    profile = get_object_or_404(TeacherStyleProfile, id=profile_id, user=request.user)
    profile.delete()
    messages.success(request, '风格画像已删除')
    return redirect('profile_list')
