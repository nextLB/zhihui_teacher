from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.conf import settings
import os
import json
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
            return redirect('analysis:upload_audio')
        
        # 获取文件扩展名
        file_ext = audio_file.name.split('.')[-1].lower() if '.' in audio_file.name else 'other'
        if file_ext not in ['mp3', 'wav', 'm4a']:
            messages.error(request, '不支持的文件格式，请上传MP3、WAV或M4A文件')
            return redirect('analysis:upload_audio')
        
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
        return redirect('analysis:audio_detail', audio_id=audio.id)
    
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
            return redirect('analysis:upload_video')
        
        # 获取文件扩展名
        file_ext = video_file.name.split('.')[-1].lower() if '.' in video_file.name else 'other'
        if file_ext not in ['mp4', 'avi', 'mov']:
            messages.error(request, '不支持的文件格式，请上传MP4、AVI或MOV文件')
            return redirect('analysis:upload_video')
        
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
        return redirect('analysis:video_detail', video_id=video.id)
    
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
        
        result = analyze_audio(audio.file.path, audio_id)
        
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
        result = analyze_video(video.file.path, video_id)
        
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
            key_frames=result.get('key_frames', []),
            captured_frames=result.get('captured_frames', [])
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
        return redirect('analysis:audio_detail', audio_id=audio.id)
    
    # 启动后台分析任务
    thread = threading.Thread(target=run_audio_analysis, args=(audio_id,))
    thread.start()
    
    messages.success(request, '音频分析任务已启动，请稍后刷新页面查看结果')
    return redirect('analysis:audio_detail', audio_id=audio.id)


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
        return redirect('analysis:video_detail', video_id=video.id)
    
    # 启动后台分析任务
    thread = threading.Thread(target=run_video_analysis, args=(video_id,))
    thread.start()
    
    messages.success(request, '视频分析任务已启动，请稍后刷新页面查看结果')
    return redirect('analysis:video_detail', video_id=video.id)


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
            return redirect('analysis:create_profile')
        
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
        return redirect('analysis:profile_detail', profile_id=profile.id)
    
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
    return redirect('analysis:audio_list')


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
    return redirect('analysis:video_list')


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
    return redirect('analysis:profile_list')


@login_required
def video_analysis_progress(request, video_id):
    """
    获取视频分析进度API
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        JsonResponse - 分析进度信息
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    
    progress_file = os.path.join(settings.MEDIA_ROOT, f'video_{video_id}_progress.json')
    
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
    else:
        progress_data = {'progress': 0, 'frame_id': 0, 'total_frames': 0}
    
    return JsonResponse({
        'status': video.status,
        'progress': progress_data.get('progress', 0),
        'frame_id': progress_data.get('frame_id', 0),
        'total_frames': progress_data.get('total_frames', 0),
        'preview_path': progress_data.get('preview_path', '')
    })


@login_required
def get_video_preview(request, video_id):
    """
    获取视频分析预览图API
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        HttpResponse - 预览图
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    
    preview_path = os.path.join(settings.MEDIA_ROOT, f'video_{video_id}_preview.jpg')
    
    if os.path.exists(preview_path):
        with open(preview_path, 'rb') as f:
            return HttpResponse(f.read(), content_type='image/jpeg')
    else:
        return HttpResponse(status=404)


@login_required
def get_captured_frames(request, video_id):
    """
    获取视频分析捕获的代表性帧API
    
    参数:
        request: HttpRequest对象
        video_id: int - 视频文件ID
        
    返回:
        JsonResponse - 捕获帧信息
    """
    video = get_object_or_404(VideoFile, id=video_id, user=request.user)
    
    if video.status != 'completed':
        return JsonResponse({'error': '视频分析尚未完成'}, status=400)
    
    try:
        analysis_result = video.analysis_result
        captured_frames = analysis_result.captured_frames or []
        return JsonResponse({
            'success': True,
            'captured_frames': captured_frames
        })
    except VideoAnalysisResult.DoesNotExist:
        return JsonResponse({'error': '分析结果不存在'}, status=404)


@login_required
def data_collection(request):
    """
    数据采集页面视图
    
    参数:
        request: HttpRequest对象
        
    返回:
        HttpResponse对象 - 渲染数据采集页面
    """
    return render(request, 'analysis/data_collection.html')


@login_required
def save_collection(request):
    """
    保存采集的数据
    
    参数:
        request: HttpRequest对象
        
    返回:
        JsonResponse - 保存结果
    """
    if request.method != 'POST':
        return JsonResponse({'error': '请求方法不正确'}, status=400)
    
    try:
        collection_type = request.POST.get('type', 'both')
        title = request.POST.get('title', '采集数据')
        
        saved_files = []
        
        timestamp = int(timezone.now().timestamp())
        save_dir = os.path.join(settings.MEDIA_ROOT, 'captures')
        os.makedirs(save_dir, exist_ok=True)
        
        if collection_type in ['video', 'both']:
            if 'video_file' in request.FILES:
                video_file = request.FILES['video_file']
                video_filename = f"capture_{timestamp}.mp4"
                video_path = os.path.join(save_dir, video_filename)
                
                try:
                    import subprocess
                    temp_webm = os.path.join(save_dir, f"temp_{timestamp}.webm")
                    with open(temp_webm, 'wb') as f:
                        for chunk in video_file.chunks():
                            f.write(chunk)
                    
                    subprocess.run([
                        'ffmpeg', '-i', temp_webm, '-c:v', 'libx264', 
                        '-preset', 'fast', '-crf', '23', '-c:a', 'aac', 
                        '-b:a', '128k', '-y', video_path
                    ], check=True, capture_output=True)
                    
                    os.remove(temp_webm)
                    file_size = os.path.getsize(video_path)
                except Exception as e:
                    import shutil
                    shutil.copy(temp_webm, video_path.replace('.mp4', '.webm'))
                    video_filename = f"capture_{timestamp}.webm"
                    video_path = video_path.replace('.mp4', '.webm')
                    file_size = os.path.getsize(video_path)
                    os.remove(temp_webm) if os.path.exists(temp_webm) else None
                
                full_path = os.path.join('captures', video_filename)
                video = VideoFile.objects.create(
                    user=request.user,
                    title=f"{title} - 视频",
                    file=full_path,
                    file_type='mp4' if video_filename.endswith('.mp4') else 'webm',
                    file_size=file_size,
                    status='pending'
                )
                saved_files.append({'type': 'video', 'id': video.id, 'path': video_path})
        
        if collection_type in ['audio', 'both']:
            if 'audio_file' in request.FILES:
                audio_file = request.FILES['audio_file']
                audio_filename = f"capture_{timestamp}.mp3"
                audio_path = os.path.join(save_dir, audio_filename)
                
                try:
                    temp_webm = os.path.join(save_dir, f"temp_audio_{timestamp}.webm")
                    with open(temp_webm, 'wb') as f:
                        for chunk in audio_file.chunks():
                            f.write(chunk)
                    
                    subprocess.run([
                        'ffmpeg', '-i', temp_webm, '-acodec', 'libmp3lame',
                        '-ab', '128k', '-y', audio_path
                    ], check=True, capture_output=True)
                    
                    os.remove(temp_webm)
                    file_size = os.path.getsize(audio_path)
                except Exception as e:
                    import shutil
                    shutil.copy(temp_webm, audio_path.replace('.mp3', '.webm'))
                    audio_filename = f"capture_{timestamp}.webm"
                    audio_path = audio_path.replace('.mp3', '.webm')
                    file_size = os.path.getsize(audio_path)
                    os.remove(temp_webm) if os.path.exists(temp_webm) else None
                
                full_path = os.path.join('captures', audio_filename)
                audio = AudioFile.objects.create(
                    user=request.user,
                    title=f"{title} - 音频",
                    file=full_path,
                    file_type='mp3' if audio_filename.endswith('.mp3') else 'webm',
                    file_size=file_size,
                    status='pending'
                )
                saved_files.append({'type': 'audio', 'id': audio.id, 'path': audio_path})
        
        return JsonResponse({
            'success': True,
            'message': f'成功保存 {len(saved_files)} 个文件',
            'files': saved_files
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def audio_analysis_progress(request, audio_id):
    """
    获取音频分析进度API
    
    参数:
        request: HttpRequest对象
        audio_id: int - 音频文件ID
        
    返回:
        JsonResponse - 分析进度信息
    """
    audio = get_object_or_404(AudioFile, id=audio_id, user=request.user)
    
    progress_file = os.path.join(settings.MEDIA_ROOT, f'audio_{audio_id}_progress.json')
    
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress_data = json.load(f)
    else:
        progress_data = {'stage': 'processing', 'progress': 0}
    
    return JsonResponse({
        'status': audio.status,
        'stage': progress_data.get('stage', 'processing'),
        'duration': progress_data.get('duration', 0),
        'text_length': progress_data.get('text_length', 0)
    })


@login_required
def generate_profile_image(request, profile_id):
    """
    生成风格画像图片
    """
    profile = get_object_or_404(TeacherStyleProfile, id=profile_id, user=request.user)
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        
        plt.rcParams['axes.unicode_minus'] = False
        
        fig = plt.figure(figsize=(12, 8), facecolor='white')
        
        radar_data = profile.radar_data
        original_indicators = [ind['name'] for ind in radar_data.get('indicators', [])]
        values = radar_data.get('values', [])
        
        zh_to_en = {
            '语速': 'Speech Rate',
            '语气多样性': 'Tone Diversity',
            '提问比例': 'Question Ratio',
            '站立比例': 'Standing Ratio',
            '走动比例': 'Walking Ratio',
            '板书比例': 'Writing Ratio',
            '互动频率': 'Interaction',
            '活动度': 'Activity'
        }
        indicators = [zh_to_en.get(ind, ind) for ind in original_indicators]
        
        angles = np.linspace(0, 2*np.pi, len(indicators), endpoint=False).tolist()
        values_plot = values + [values[0]] if values else [0]
        angles_plot = angles + [angles[0]] if angles else [0]
        
        ax1 = fig.add_subplot(121, polar=True)
        ax1.fill(angles_plot, values_plot, alpha=0.25, color='blue')
        ax1.plot(angles_plot, values_plot, 'o-', linewidth=2, color='blue')
        ax1.set_xticks(angles)
        ax1.set_xticklabels(indicators, fontsize=10)
        
        style_type_map = {
            'active_interactive': 'Active Interactive',
            'calm_lecture': 'Calm Lecture',
            'walking_guide': 'Walking Guide',
            'mixed': 'Mixed Style'
        }
        type_display = style_type_map.get(profile.style_type, profile.style_type)
        ax1.set_title(f'{profile.name}\n({type_display})', fontsize=14, fontweight='bold')
        
        ax2 = fig.add_subplot(122)
        ax2.axis('off')
        
        tags_text = ', '.join(profile.style_tags) if profile.style_tags else 'N/A'
        info_lines = [
            f'Style Type: {type_display}',
            '',
            f'Tags: {tags_text}',
            '',
            f'Created: {profile.created_at.strftime("%Y-%m-%d %H:%M")}',
            '',
            'Features:',
            f'  Speech Rate: {profile.feature_vector.get("speech_rate_norm", 0):.2f}',
            f'  Tone Diversity: {profile.feature_vector.get("tone_diversity", 0):.2f}',
            f'  Question Ratio: {profile.feature_vector.get("question_ratio", 0):.2f}',
            f'  Walking Ratio: {profile.feature_vector.get("walking_ratio", 0):.2f}',
            f'  Writing Ratio: {profile.feature_vector.get("writing_ratio", 0):.2f}',
            f'  Interaction: {profile.feature_vector.get("interaction_ratio", 0):.2f}',
            f'  Activity: {profile.feature_vector.get("movement_activity", 0):.2f}'
        ]
        
        y_pos = 0.95
        for line in info_lines:
            ax2.text(0.1, y_pos, line, transform=ax2.transAxes, fontsize=11,
                    verticalalignment='top', fontfamily='sans-serif')
            y_pos -= 0.07
        
        plt.tight_layout()
        
        img_path = os.path.join(settings.MEDIA_ROOT, 'profile_images')
        os.makedirs(img_path, exist_ok=True)
        
        save_path = os.path.join(img_path, f'profile_{profile_id}.png')
        plt.savefig(save_path, dpi=100, bbox_inches='tight', facecolor='white')
        plt.close()
        
        profile.profile_image_url = f'/media/profile_images/profile_{profile_id}.png'
        profile.save()
        
        return JsonResponse({'success': True, 'image_url': profile.profile_image_url})
        
    except ImportError as e:
        return JsonResponse({'success': False, 'error': f'缺少依赖库: {str(e)}'}, status=500)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
def profile_detail(request, profile_id):
    """
    风格画像详情视图
    """
    profile = get_object_or_404(TeacherStyleProfile, id=profile_id, user=request.user)
    
    if not profile.radar_data or not profile.radar_data.get('indicators'):
        audio_features = {}
        video_features = {}
        
        if profile.audio_result:
            audio_features = {
                'speech_rate': profile.audio_result.speech_rate,
                'tone_type': profile.audio_result.tone_type,
                'question_types': profile.audio_result.question_types,
                'utterance_length_avg': profile.audio_result.utterance_length_avg
            }
        
        if profile.video_result:
            video_features = {
                'teacher_standing_ratio': profile.video_result.teacher_standing_ratio,
                'teacher_walking_ratio': profile.video_result.teacher_walking_ratio,
                'teacher_writing_ratio': profile.video_result.teacher_writing_ratio,
                'teacher_facing_students_ratio': profile.video_result.teacher_facing_students_ratio,
                'student_hand_raising_count': profile.video_result.student_hand_raising_count,
                'interaction_count': profile.video_result.interaction_count
            }
        
        profile_data = build_style_profile(audio_features, video_features)
        profile.radar_data = profile_data.get('radar_data', {})
        profile.feature_vector = profile_data.get('feature_vector', {})
        profile.save()
    
    return render(request, 'analysis/profile_detail.html', {
        'profile': profile,
        'profile_image': profile.profile_image_url
    })
