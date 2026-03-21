"""
风格画像构建模块
此模块提供教师风格画像的构建和聚类功能
"""

# import numpy as np  # TODO: 安装 numpy: pip install numpy
from typing import Dict, Any, List, Optional, Tuple


class FeatureFusion:
    """
    特征融合器
    将语音特征和行为特征进行融合
    """
    
    @staticmethod
    def fuse_features(
        audio_features: Dict[str, Any],
        video_features: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        融合语音和视频特征
        """
        speech_rate = audio_features.get('speech_rate', 0)
        speech_rate_norm = min(speech_rate / 200.0, 1.0)
        
        tone_type = audio_features.get('tone_type', '中性型')
        tone_diversity = 0.0
        if tone_type in ['鼓励型', '引导型', '讲授型']:
            tone_diversity = 0.7
        elif tone_type != '中性型':
            tone_diversity = 0.5
        
        question_types = audio_features.get('question_types', {})
        total_questions = sum(question_types.values()) if question_types else 0
        question_ratio = min(total_questions / 10.0, 1.0)
        
        standing_ratio = video_features.get('teacher_standing_ratio', 0)
        walking_ratio = video_features.get('teacher_walking_ratio', 0)
        writing_ratio = video_features.get('teacher_writing_ratio', 0)
        facing_ratio = video_features.get('teacher_facing_students_ratio', 0)
        
        interaction_count = video_features.get('interaction_count', 0)
        interaction_ratio = min(interaction_count / 20.0, 1.0)
        
        movement_activity = walking_ratio * 0.4 + standing_ratio * 0.3 + writing_ratio * 0.3
        
        return {
            'speech_rate_norm': speech_rate_norm,
            'tone_diversity': tone_diversity,
            'question_ratio': question_ratio,
            'standing_ratio': standing_ratio,
            'walking_ratio': walking_ratio,
            'writing_ratio': writing_ratio,
            'facing_ratio': facing_ratio,
            'interaction_ratio': interaction_ratio,
            'movement_activity': min(movement_activity, 1.0)
        }


class StyleCluster:
    """
    风格聚类器
    使用K-means等算法对教师风格进行聚类
    """
    
    STYLE_LABELS = {
        0: '活跃互动型',
        1: '沉稳讲授型',
        2: '走动引导型',
        3: '混合型'
    }
    
    def __init__(self, n_clusters: int = 4):
        """
        初始化聚类器
        
        参数:
            n_clusters: int - 聚类数量，默认4
        """
        self.n_clusters = n_clusters
        self.model = None
        self.fitted = False
    
    def fit(self, features_list: List[Dict[str, float]]) -> None:
        """
        训练聚类模型
        """
        pass
    
    def predict(self, features: Dict[str, float]) -> Tuple[str, List[str]]:
        """
        预测教师风格类型
        """
        return self._rule_based_prediction(features)
    
    def _rule_based_prediction(self, features: Dict[str, float]) -> Tuple[str, List[str]]:
        """
        基于规则的风格判断
        """
        style_tags = []
        
        interaction = features.get('interaction_ratio', 0)
        walking = features.get('walking_ratio', 0)
        writing = features.get('writing_ratio', 0)
        movement = features.get('movement_activity', 0)
        
        if interaction > 0.5 and features.get('question_ratio', 0) > 0.3:
            style_type = 'active_interactive'
            style_tags.append('互动频繁')
            style_tags.append('提问活跃')
        elif writing > 0.4 and interaction < 0.3:
            style_type = 'calm_lecture'
            style_tags.append('沉稳讲授')
            style_tags.append('板书丰富')
        elif walking > 0.3 and movement > 0.5:
            style_type = 'walking_guide'
            style_tags.append('走动引导')
            style_tags.append('活动范围大')
        else:
            style_type = 'mixed'
            style_tags.append('综合型')
        
        if features.get('tone_diversity', 0) > 0.5:
            style_tags.append('语气丰富')
        
        if features.get('speech_rate_norm', 0) > 0.7:
            style_tags.append('语速较快')
        elif features.get('speech_rate_norm', 0) < 0.3:
            style_tags.append('语速较慢')
        
        return style_type, style_tags
    
    def _generate_style_tags(self, features: Dict[str, float]) -> List[str]:
        """
        生成个性化风格标签
        """
        return []


class RadarChartGenerator:
    """
    雷达图生成器
    生成用于前端展示的雷达图数据
    """
    
    @staticmethod
    def generate_radar_data(features: Dict[str, float]) -> Dict[str, Any]:
        """
        生成雷达图数据
        """
        return {
            'indicators': [
                {'name': '语速', 'max': 1.0},
                {'name': '语气多样性', 'max': 1.0},
                {'name': '提问比例', 'max': 1.0},
                {'name': '站立比例', 'max': 1.0},
                {'name': '走动比例', 'max': 1.0},
                {'name': '板书比例', 'max': 1.0},
                {'name': '互动频率', 'max': 1.0},
                {'name': '活动度', 'max': 1.0},
            ],
            'values': [
                round(features.get('speech_rate_norm', 0), 2),
                round(features.get('tone_diversity', 0), 2),
                round(features.get('question_ratio', 0), 2),
                round(features.get('standing_ratio', 0), 2),
                round(features.get('walking_ratio', 0), 2),
                round(features.get('writing_ratio', 0), 2),
                round(features.get('interaction_ratio', 0), 2),
                round(features.get('movement_activity', 0), 2),
            ]
        }


class TimelineGenerator:
    """
    时序图生成器
    生成语速与姿态的时序数据
    """
    
    @staticmethod
    def generate_timeline_data(
        audio_timeline: Optional[Dict[str, Any]] = None,
        video_timeline: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        生成时序图数据
        """
        result = {}
        
        if audio_timeline:
            result['speech_rate'] = {
                'timestamps': audio_timeline.get('timestamps', []),
                'values': audio_timeline.get('speech_rates', [])
            }
        
        if video_timeline:
            posture_map = {'站立': 1, '走动': 2, '板书': 3, '面向学生': 4}
            postures = video_timeline.get('postures', [])
            posture_values = [posture_map.get(p, 0) for p in postures]
            
            result['posture'] = {
                'timestamps': video_timeline.get('timestamps', []),
                'values': posture_values
            }
        
        return result


def build_style_profile(
    audio_features: Dict[str, Any],
    video_features: Dict[str, Any],
    audio_timeline: Optional[Dict[str, Any]] = None,
    video_timeline: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    构建完整的教师风格画像
    
    参数:
        audio_features: Dict[str, Any] - 语音分析特征
        video_features: Dict[str, Any] - 视频分析特征
        audio_timeline: Optional[Dict[str, Any]] - 语音时序数据
        video_timeline: Optional[Dict[str, Any]] - 视频时序数据
        
    返回:
        Dict[str, Any]: 完整的风格画像数据，包含:
            - style_type: 风格类型
            - style_tags: 风格标签列表
            - feature_vector: 融合特征向量
            - radar_data: 雷达图数据
            - timeline_data: 时序图数据
    """
    # 步骤1: 特征融合
    fused_features = FeatureFusion.fuse_features(audio_features, video_features)
    
    # 步骤2: 风格聚类
    cluster = StyleCluster()
    style_type, style_tags = cluster.predict(fused_features)
    
    # 步骤3: 生成雷达图数据
    radar_data = RadarChartGenerator.generate_radar_data(fused_features)
    
    # 步骤4: 生成时序图数据
    timeline_data = TimelineGenerator.generate_timeline_data(audio_timeline, video_timeline)
    
    return {
        'style_type': style_type,
        'style_tags': style_tags,
        'feature_vector': fused_features,
        'radar_data': radar_data,
        'timeline_data': timeline_data
    }
