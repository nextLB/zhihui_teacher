import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class BehaviorFeatureVector:
    teacher_standing_ratio: float
    teacher_walking_ratio: float
    teacher_writing_ratio: float
    teacher_facing_student_ratio: float
    student_hand_raise_count: int
    student_stand_up_count: int
    student_head_down_count: int
    interaction_frequency: float
    interaction_duration_ratio: float
    walking_range: float
    walking_speed: float
    pose_transition_count: int
    total_frames: int
    total_duration: float
    
    def to_list(self) -> List[float]:
        return [
            self.teacher_standing_ratio,
            self.teacher_walking_ratio,
            self.teacher_writing_ratio,
            self.teacher_facing_student_ratio,
            self.student_hand_raise_count,
            self.student_stand_up_count,
            self.student_head_down_count,
            self.interaction_frequency,
            self.interaction_duration_ratio,
            self.walking_range,
            self.walking_speed,
            self.pose_transition_count,
            self.total_frames,
            self.total_duration
        ]
    
    def to_dict(self) -> Dict:
        return {
            "teacher_standing_ratio": self.teacher_standing_ratio,
            "teacher_walking_ratio": self.teacher_walking_ratio,
            "teacher_writing_ratio": self.teacher_writing_ratio,
            "teacher_facing_student_ratio": self.teacher_facing_student_ratio,
            "student_hand_raise_count": self.student_hand_raise_count,
            "student_stand_up_count": self.student_stand_up_count,
            "student_head_down_count": self.student_head_down_count,
            "interaction_frequency": self.interaction_frequency,
            "interaction_duration_ratio": self.interaction_duration_ratio,
            "walking_range": self.walking_range,
            "walking_speed": self.walking_speed,
            "pose_transition_count": self.pose_transition_count,
            "total_frames": self.total_frames,
            "total_duration": self.total_duration
        }
    
    def normalize(self, min_values: Dict[str, float], max_values: Dict[str, float]) -> 'BehaviorFeatureVector':
        normalized = {}
        
        for key in ['teacher_standing_ratio', 'teacher_walking_ratio', 
                    'teacher_writing_ratio', 'teacher_facing_student_ratio',
                    'interaction_frequency', 'interaction_duration_ratio']:
            val = getattr(self, key)
            min_val = min_values.get(key, 0)
            max_val = max_values.get(key, 1)
            if max_val > min_val:
                normalized[key] = (val - min_val) / (max_val - min_val)
            else:
                normalized[key] = 0
        
        for key in ['student_hand_raise_count', 'student_stand_up_count', 
                    'student_head_down_count', 'pose_transition_count']:
            val = getattr(self, key)
            min_val = min_values.get(key, 0)
            max_val = max_values.get(key, 1)
            if max_val > min_val:
                normalized[key] = (val - min_val) / (max_val - min_val)
            else:
                normalized[key] = 0
        
        for key in ['walking_range', 'walking_speed']:
            val = getattr(self, key)
            min_val = min_values.get(key, 0)
            max_val = max_values.get(key, 1)
            if max_val > min_val:
                normalized[key] = (val - min_val) / (max_val - min_val)
            else:
                normalized[key] = 0
        
        normalized['total_frames'] = self.total_frames
        normalized['total_duration'] = self.total_duration
        
        return BehaviorFeatureVector(**normalized)


class FeatureExtractor:
    POSE_LABELS = ["站立", "走动", "板书", "面向学生"]
    BEHAVIOR_LABELS = ["举手", "起立", "低头", "正常"]
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.statistics = None
    
    def set_statistics(self, statistics):
        self.statistics = statistics
    
    def extract_features(self) -> BehaviorFeatureVector:
        if self.statistics is None:
            logger.warning("未设置统计数据")
            return self._empty_feature_vector()
        
        summary = self.statistics.get_summary()
        
        pose_ratios = summary.get("teacher_pose_time_ratio", {})
        
        standing_ratio = pose_ratios.get("站立", 0.0)
        walking_ratio = pose_ratios.get("走动", 0.0)
        writing_ratio = pose_ratios.get("板书", 0.0)
        facing_student_ratio = pose_ratios.get("面向学生", 0.0)
        
        behavior_counts = summary.get("student_behavior_counts", {})
        
        hand_raise_count = behavior_counts.get("举手", 0)
        stand_up_count = behavior_counts.get("起立", 0)
        head_down_count = behavior_counts.get("低头", 0)
        
        interaction_frequency = summary.get("interaction_frequency", 0.0)
        interaction_duration_ratio = summary.get("interaction_duration_ratio", 0.0)
        
        walking_range = summary.get("walking_range", 0.0)
        walking_speed = summary.get("walking_speed", 0.0)
        
        pose_transition_count = summary.get("pose_transition_count", 0)
        
        total_frames = summary.get("total_frames", 0)
        total_duration = summary.get("total_duration", 0.0)
        
        return BehaviorFeatureVector(
            teacher_standing_ratio=standing_ratio,
            teacher_walking_ratio=walking_ratio,
            teacher_writing_ratio=writing_ratio,
            teacher_facing_student_ratio=facing_student_ratio,
            student_hand_raise_count=hand_raise_count,
            student_stand_up_count=stand_up_count,
            student_head_down_count=head_down_count,
            interaction_frequency=interaction_frequency,
            interaction_duration_ratio=interaction_duration_ratio,
            walking_range=walking_range,
            walking_speed=walking_speed,
            pose_transition_count=pose_transition_count,
            total_frames=total_frames,
            total_duration=total_duration
        )
    
    def _empty_feature_vector(self) -> BehaviorFeatureVector:
        return BehaviorFeatureVector(
            teacher_standing_ratio=0.0,
            teacher_walking_ratio=0.0,
            teacher_writing_ratio=0.0,
            teacher_facing_student_ratio=0.0,
            student_hand_raise_count=0,
            student_stand_up_count=0,
            student_head_down_count=0,
            interaction_frequency=0.0,
            interaction_duration_ratio=0.0,
            walking_range=0.0,
            walking_speed=0.0,
            pose_transition_count=0,
            total_frames=0,
            total_duration=0.0
        )
    
    def extract_temporal_features(self, window_size: int = 300) -> List[BehaviorFeatureVector]:
        if self.statistics is None:
            return []
        
        features = []
        
        pose_segments = self.statistics.teacher_pose_segments
        behavior_events = self.statistics.student_behavior_events
        interaction_events = self.statistics.interaction_events
        
        if not pose_segments:
            return []
        
        start_time = pose_segments[0].start_time
        end_time = pose_segments[-1].end_time
        total_time = end_time - start_time
        
        window_count = int(total_time / window_size) + 1
        
        for i in range(window_count):
            window_start = start_time + i * window_size
            window_end = min(window_start + window_size, end_time)
            
            pose_time = {"站立": 0.0, "走动": 0.0, "板书": 0.0, "面向学生": 0.0}
            
            for segment in pose_segments:
                if segment.start_time >= window_start and segment.end_time <= window_end:
                    pose_time[segment.pose_type] += segment.duration
                elif segment.start_time < window_end and segment.end_time > window_start:
                    overlap_start = max(segment.start_time, window_start)
                    overlap_end = min(segment.end_time, window_end)
                    pose_time[segment.pose_type] += overlap_end - overlap_start
            
            window_duration = window_end - window_start
            
            behavior_count = {"举手": 0, "起立": 0, "低头": 0}
            for event in behavior_events:
                if window_start <= event["timestamp"] < window_end:
                    behavior_count[event["behavior"]] += 1
            
            interaction_count = 0
            for event in interaction_events:
                if window_start <= event.timestamp < window_end:
                    interaction_count += 1
            
            interaction_freq = interaction_count / window_duration if window_duration > 0 else 0
            
            window_features = BehaviorFeatureVector(
                teacher_standing_ratio=pose_time["站立"] / window_duration if window_duration > 0 else 0,
                teacher_walking_ratio=pose_time["走动"] / window_duration if window_duration > 0 else 0,
                teacher_writing_ratio=pose_time["板书"] / window_duration if window_duration > 0 else 0,
                teacher_facing_student_ratio=pose_time["面向学生"] / window_duration if window_duration > 0 else 0,
                student_hand_raise_count=behavior_count["举手"],
                student_stand_up_count=behavior_count["起立"],
                student_head_down_count=behavior_count["低头"],
                interaction_frequency=interaction_freq,
                interaction_duration_ratio=0.0,
                walking_range=0.0,
                walking_speed=0.0,
                pose_transition_count=0,
                total_frames=0,
                total_duration=window_duration
            )
            
            features.append(window_features)
        
        return features
    
    def calculate_engagement_score(self) -> float:
        features = self.extract_features()
        
        writing_weight = 0.3
        interaction_weight = 0.4
        facing_weight = 0.3
        
        writing_score = features.teacher_writing_ratio
        interaction_score = min(features.interaction_frequency * 10, 1.0)
        facing_score = features.teacher_facing_student_ratio
        
        engagement_score = (
            writing_weight * writing_score +
            interaction_weight * interaction_score +
            facing_score * facing_score
        )
        
        return min(engagement_score, 1.0)
    
    def calculate_attention_score(self) -> float:
        features = self.extract_features()
        
        hand_raise_weight = 0.4
        stand_up_weight = 0.3
        head_down_penalty_weight = 0.3
        
        hand_raise_score = min(features.student_hand_raise_count / 10, 1.0)
        stand_up_score = min(features.student_stand_up_count / 5, 1.0)
        head_down_penalty = min(features.student_head_down_count / 20, 1.0)
        
        attention_score = (
            hand_raise_weight * hand_raise_score +
            stand_up_weight * stand_up_score +
            head_down_penalty_weight * (1 - head_down_penalty)
        )
        
        return min(attention_score, 1.0)
    
    def compare_with_baseline(self, baseline_features: BehaviorFeatureVector) -> Dict:
        current_features = self.extract_features()
        
        differences = {}
        
        feature_names = [
            "teacher_standing_ratio", "teacher_walking_ratio", "teacher_writing_ratio",
            "teacher_facing_student_ratio", "student_hand_raise_count", "student_stand_up_count",
            "student_head_down_count", "interaction_frequency", "walking_range"
        ]
        
        for name in feature_names:
            current_val = getattr(current_features, name)
            baseline_val = getattr(baseline_features, name)
            differences[name] = current_val - baseline_val
        
        return differences
    
    def export_features(self, path: str):
        import json
        
        features = self.extract_features()
        
        data = {
            "feature_vector": features.to_dict(),
            "engagement_score": self.calculate_engagement_score(),
            "attention_score": self.calculate_attention_score()
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"特征向量已导出: {path}")
    
    def load_features(self, path: str) -> BehaviorFeatureVector:
        import json
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        feature_dict = data.get("feature_vector", {})
        
        return BehaviorFeatureVector(
            teacher_standing_ratio=feature_dict.get("teacher_standing_ratio", 0),
            teacher_walking_ratio=feature_dict.get("teacher_walking_ratio", 0),
            teacher_writing_ratio=feature_dict.get("teacher_writing_ratio", 0),
            teacher_facing_student_ratio=feature_dict.get("teacher_facing_student_ratio", 0),
            student_hand_raise_count=feature_dict.get("student_hand_raise_count", 0),
            student_stand_up_count=feature_dict.get("student_stand_up_count", 0),
            student_head_down_count=feature_dict.get("student_head_down_count", 0),
            interaction_frequency=feature_dict.get("interaction_frequency", 0),
            interaction_duration_ratio=feature_dict.get("interaction_duration_ratio", 0),
            walking_range=feature_dict.get("walking_range", 0),
            walking_speed=feature_dict.get("walking_speed", 0),
            pose_transition_count=feature_dict.get("pose_transition_count", 0),
            total_frames=feature_dict.get("total_frames", 0),
            total_duration=feature_dict.get("total_duration", 0)
        )
    
    def __repr__(self):
        return f"FeatureExtractor(statistics={self.statistics is not None})"