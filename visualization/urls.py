from django.urls import path
from . import views

app_name = 'visualization'

urlpatterns = [
    # 图表数据API
    path('api/radar/<int:profile_id>/', views.radar_chart, name='radar_chart'),
    path('api/timeline/<int:profile_id>/', views.timeline_chart, name='timeline_chart'),
    path('api/tone-distribution/<int:audio_id>/', views.tone_distribution, name='tone_distribution'),
    path('api/question-types/<int:audio_id>/', views.question_types_chart, name='question_types_chart'),
    path('api/student-behavior/<int:video_id>/', views.student_behavior_chart, name='student_behavior_chart'),
    path('api/posture-timeline/<int:video_id>/', views.posture_timeline, name='posture_timeline'),
]
