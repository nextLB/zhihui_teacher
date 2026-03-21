from django.db import models
from django.contrib.auth.models import User


class AudioFile(models.Model):
    """
    音频文件模型
    用于存储用户上传的课堂音频文件
    """
    FILE_TYPE_CHOICES = [
        ('mp3', 'MP3'),
        ('wav', 'WAV'),
        ('m4a', 'M4A'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='audio_files', verbose_name='上传用户')
    title = models.CharField(max_length=200, verbose_name='音频标题')
    description = models.TextField(blank=True, verbose_name='描述')
    file = models.FileField(upload_to='audio/%Y/%m/%d/', verbose_name='音频文件')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other', verbose_name='文件类型')
    duration = models.IntegerField(default=0, verbose_name='时长(秒)')
    file_size = models.IntegerField(default=0, verbose_name='文件大小(字节)')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    processed_time = models.DateTimeField(null=True, blank=True, verbose_name='处理完成时间')

    class Meta:
        db_table = 'audio_file'
        verbose_name = '音频文件'
        verbose_name_plural = '音频文件'
        ordering = ['-upload_time']

    def __str__(self):
        return self.title


class VideoFile(models.Model):
    """
    视频文件模型
    用于存储用户上传的课堂视频文件
    """
    FILE_TYPE_CHOICES = [
        ('mp4', 'MP4'),
        ('avi', 'AVI'),
        ('mov', 'MOV'),
        ('other', '其他'),
    ]
    
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('processing', '处理中'),
        ('completed', '已完成'),
        ('failed', '失败'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='video_files', verbose_name='上传用户')
    title = models.CharField(max_length=200, verbose_name='视频标题')
    description = models.TextField(blank=True, verbose_name='描述')
    file = models.FileField(upload_to='video/%Y/%m/%d/', verbose_name='视频文件')
    file_type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES, default='other', verbose_name='文件类型')
    duration = models.IntegerField(default=0, verbose_name='时长(秒)')
    file_size = models.IntegerField(default=0, verbose_name='文件大小(字节)')
    frame_count = models.IntegerField(default=0, verbose_name='总帧数')
    fps = models.FloatField(default=0, verbose_name='帧率')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='处理状态')
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name='上传时间')
    processed_time = models.DateTimeField(null=True, blank=True, verbose_name='处理完成时间')

    class Meta:
        db_table = 'video_file'
        verbose_name = '视频文件'
        verbose_name_plural = '视频文件'
        ordering = ['-upload_time']

    def __str__(self):
        return self.title


class AudioAnalysisResult(models.Model):
    """
    语音分析结果模型
    存储语音分析的各种特征数据
    """
    audio_file = models.OneToOneField(AudioFile, on_delete=models.CASCADE, related_name='analysis_result', verbose_name='音频文件')
    
    # 基础声学特征
    speech_rate = models.FloatField(default=0, verbose_name='语速(字/分钟)')
    pitch_frequency = models.FloatField(default=0, verbose_name='音高基频(Hz)')
    short_time_energy = models.FloatField(default=0, verbose_name='短时能量')
    mfcc = models.JSONField(default=dict, verbose_name='MFCC特征')
    
    # 语气识别结果
    tone_type = models.CharField(max_length=50, default='中性型', verbose_name='语气类型')
    tone_confidence = models.FloatField(default=0, verbose_name='语气识别置信度')
    
    # 语义特征
    transcribed_text = models.TextField(blank=True, verbose_name='转写文本')
    question_types = models.JSONField(default=dict, verbose_name='提问类型统计')
    utterance_length_avg = models.FloatField(default=0, verbose_name='平均话语长度')
    
    # 处理信息
    valid_speech_duration = models.IntegerField(default=0, verbose_name='有效语音时长(秒)')
    silence_duration = models.IntegerField(default=0, verbose_name='静音时长(秒)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='分析时间')

    class Meta:
        db_table = 'audio_analysis_result'
        verbose_name = '语音分析结果'
        verbose_name_plural = '语音分析结果'

    def __str__(self):
        return f"{self.audio_file.title} - 分析结果"


class VideoAnalysisResult(models.Model):
    """
    视频分析结果模型
    存储视频行为分析的各种特征数据
    """
    video_file = models.OneToOneField(VideoFile, on_delete=models.CASCADE, related_name='analysis_result', verbose_name='视频文件')
    
    # 教师姿态统计
    teacher_standing_ratio = models.FloatField(default=0, verbose_name='站立比例')
    teacher_walking_ratio = models.FloatField(default=0, verbose_name='走动比例')
    teacher_writing_ratio = models.FloatField(default=0, verbose_name='板书比例')
    teacher_facing_students_ratio = models.FloatField(default=0, verbose_name='面向学生比例')
    teacher_posture_timeline = models.JSONField(default=list, verbose_name='姿态时序数据')
    
    # 学生行为统计
    student_hand_raising_count = models.IntegerField(default=0, verbose_name='学生举手次数')
    student_standing_count = models.IntegerField(default=0, verbose_name='学生起立次数')
    student_head_down_count = models.IntegerField(default=0, verbose_name='学生低头次数')
    student_behavior_timeline = models.JSONField(default=list, verbose_name='学生行为时序')
    
    # 课堂互动统计
    interaction_count = models.IntegerField(default=0, verbose_name='互动次数')
    teacher_movement_range = models.FloatField(default=0, verbose_name='教师活动范围')
    student_attention_ratio = models.FloatField(default=0, verbose_name='学生注意力比例')
    
    # 关键帧提取
    key_frames = models.JSONField(default=list, verbose_name='关键帧路径列表')
    
    # 捕获的代表性帧（带识别标注的图像）
    captured_frames = models.JSONField(default=list, verbose_name='捕获的代表性帧列表')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='分析时间')

    class Meta:
        db_table = 'video_analysis_result'
        verbose_name = '视频分析结果'
        verbose_name_plural = '视频分析结果'

    def __str__(self):
        return f"{self.video_file.title} - 分析结果"


class TeacherStyleProfile(models.Model):
    """
    教师风格画像模型
    整合语音和视频分析结果，生成综合风格画像
    """
    STYLE_TYPE_CHOICES = [
        ('active_interactive', '活跃互动型'),
        ('calm_lecture', '沉稳讲授型'),
        ('walking_guide', '走动引导型'),
        ('mixed', '混合型'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='style_profiles', verbose_name='所属用户')
    name = models.CharField(max_length=100, verbose_name='画像名称')
    
    # 关联的分析结果
    audio_result = models.ForeignKey(AudioAnalysisResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile', verbose_name='语音分析结果')
    video_result = models.ForeignKey(VideoAnalysisResult, on_delete=models.SET_NULL, null=True, blank=True, related_name='profile', verbose_name='视频分析结果')
    
    # 风格类型
    style_type = models.CharField(max_length=50, choices=STYLE_TYPE_CHOICES, default='mixed', verbose_name='风格类型')
    style_tags = models.JSONField(default=list, verbose_name='风格标签列表')
    
    # 融合特征向量
    feature_vector = models.JSONField(default=dict, verbose_name='融合特征向量')
    
    # 雷达图数据
    radar_data = models.JSONField(default=dict, verbose_name='雷达图数据')
    
    # 时序数据
    timeline_data = models.JSONField(default=dict, verbose_name='时序图数据')
    
    # 风格画像图片URL
    profile_image_url = models.URLField(null=True, blank=True, verbose_name='风格画像图片URL')
    
    # 创建时间
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        db_table = 'teacher_style_profile'
        verbose_name = '教师风格画像'
        verbose_name_plural = '教师风格画像'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.get_style_type_display()}"
