import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class FrameAnalysis:
    frame_id: int
    timestamp: float
    teacher_poses: List[str] = field(default_factory=list)
    student_behaviors: List[str] = field(default_factory=list)
    teacher_count: int = 0
    student_count: int = 0
    interactions: List[Dict] = field(default_factory=list)


class BehaviorRecognizer:
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.interaction_distance = self.config.get("interaction_distance_threshold", 200)
        self.time_window = self.config.get("time_window", 60)
        
        self.teacher_pose_history = []
        self.student_behavior_history = []
        self.position_history = defaultdict(list)
        
        self.teacher_pose_counts = defaultdict(int)
        self.student_behavior_counts = defaultdict(int)
        self.interaction_count = 0
        
    def analyze_frame(self, detections: List, frame_id: int, 
                     timestamp: float, frame_shape: Tuple[int, int]) -> FrameAnalysis:
        analysis = FrameAnalysis(frame_id=frame_id, timestamp=timestamp)
        
        teachers = []
        students = []
        
        for det in detections:
            if det.keypoints is not None:
                teachers.append(det)
            else:
                students.append(det)
        
        analysis.teacher_count = len(teachers)
        analysis.student_count = len(students)
        
        for teacher in teachers:
            pose_result = self._estimate_pose(teacher, frame_shape)
            analysis.teacher_poses.append(pose_result.pose_type)
            self.teacher_pose_history.append({
                "frame": frame_id,
                "pose": pose_result.pose_type,
                "timestamp": timestamp
            })
            self.teacher_pose_counts[pose_result.pose_type] += 1
        
        for student in students:
            behavior_result = self._estimate_behavior(student, frame_shape)
            analysis.student_behaviors.append(behavior_result.pose_type)
            self.student_behavior_history.append({
                "frame": frame_id,
                "behavior": behavior_result.pose_type,
                "timestamp": timestamp
            })
            self.student_behavior_counts[behavior_result.pose_type] += 1
        
        if teachers and students:
            interactions = self._detect_interactions(teachers, students, frame_shape)
            analysis.interactions = interactions
            self.interaction_count += len(interactions)
        
        for teacher in teachers:
            centroid = self._get_centroid(teacher, frame_shape)
            if centroid:
                self.position_history["teacher"].append({
                    "frame": frame_id,
                    "timestamp": timestamp,
                    "x": centroid[0],
                    "y": centroid[1]
                })
        
        return analysis
    
    def _estimate_pose(self, detection, frame_shape: Tuple[int, int]) -> 'PoseResult':
        from src.pose_estimator import PoseEstimator, TeacherPose
        
        estimator = PoseEstimator(self.config)
        return estimator.estimate_teacher_pose(detection, frame_shape)
    
    def _estimate_behavior(self, detection, frame_shape: Tuple[int, int]) -> 'PoseResult':
        from src.pose_estimator import PoseEstimator, StudentBehavior
        
        estimator = PoseEstimator(self.config)
        return estimator.estimate_student_behavior(detection, frame_shape)
    
    def _detect_interactions(self, teachers: List, students: List, 
                            frame_shape: Tuple[int, int]) -> List[Dict]:
        interactions = []
        h, w = frame_shape
        
        for teacher in teachers:
            teacher_center = self._get_box_center(teacher.box)
            if teacher_center is None:
                continue
            
            for student in students:
                student_center = self._get_box_center(student.box)
                if student_center is None:
                    continue
                
                distance = np.sqrt(
                    (teacher_center[0] - student_center[0])**2 + 
                    (teacher_center[1] - student_center[1])**2
                )
                
                if distance < self.interaction_distance:
                    interactions.append({
                        "teacher_center": teacher_center,
                        "student_center": student_center,
                        "distance": distance
                    })
        
        return interactions
    
    def _get_box_center(self, box: np.ndarray) -> Optional[Tuple[float, float]]:
        if box is None or len(box) < 4:
            return None
        x_center = (box[0] + box[2]) / 2
        y_center = (box[1] + box[3]) / 2
        return (x_center, y_center)
    
    def _get_centroid(self, detection, frame_shape: Tuple[int, int]) -> Optional[Tuple[float, float]]:
        from src.pose_estimator import PoseEstimator
        return PoseEstimator.get_pose_centroid(detection, frame_shape)
    
    def get_teacher_pose_distribution(self) -> Dict[str, float]:
        if not self.teacher_pose_counts:
            return {}
        
        total = sum(self.teacher_pose_counts.values())
        return {pose: count / total for pose, count in self.teacher_pose_counts.items()}
    
    def get_student_behavior_distribution(self) -> Dict[str, float]:
        if not self.student_behavior_counts:
            return {}
        
        total = sum(self.student_behavior_counts.values())
        return {behavior: count / total for behavior, count in self.student_behavior_counts.items()}
    
    def get_walking_range(self) -> float:
        positions = self.position_history.get("teacher", [])
        if len(positions) < 2:
            return 0.0
        
        x_coords = [p["x"] for p in positions]
        y_coords = [p["y"] for p in positions]
        
        x_range = max(x_coords) - min(x_coords)
        y_range = max(y_coords) - min(y_coords)
        
        return np.sqrt(x_range**2 + y_range**2)
    
    def get_interaction_frequency(self, duration: float) -> float:
        if duration <= 0:
            return 0.0
        return self.interaction_count / duration
    
    def get_statistics(self) -> Dict:
        return {
            "teacher_pose_distribution": self.get_teacher_pose_distribution(),
            "student_behavior_distribution": self.get_student_behavior_distribution(),
            "total_interactions": self.interaction_count,
            "walking_range": self.get_walking_range(),
            "total_teacher_poses": sum(self.teacher_pose_counts.values()),
            "total_student_behaviors": sum(self.student_behavior_counts.values())
        }
    
    def reset(self):
        self.teacher_pose_history.clear()
        self.student_behavior_history.clear()
        self.position_history.clear()
        self.teacher_pose_counts.clear()
        self.student_behavior_counts.clear()
        self.interaction_count = 0
    
    def save_history(self, path: str):
        import json
        data = {
            "teacher_poses": self.teacher_pose_history,
            "student_behaviors": self.student_behavior_history,
            "statistics": self.get_statistics()
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"历史数据已保存: {path}")
    
    def load_history(self, path: str):
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.teacher_pose_history = data.get("teacher_poses", [])
        self.student_behavior_history = data.get("student_behaviors", [])
        
        for entry in self.teacher_pose_history:
            self.teacher_pose_counts[entry["pose"]] += 1
        
        for entry in self.student_behavior_history:
            self.student_behavior_counts[entry["behavior"]] += 1
        
        logger.info(f"历史数据已加载: {path}")
    
    def __repr__(self):
        return f"BehaviorRecognizer(interactions={self.interaction_count}, poses={len(self.teacher_pose_history)})"