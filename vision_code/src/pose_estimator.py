import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TeacherPose(Enum):
    STANDING = "站立"
    WALKING = "走动"
    WRITING = "板书"
    FACING_STUDENT = "面向学生"
    UNKNOWN = "未知"


class StudentBehavior(Enum):
    HAND_RAISE = "举手"
    STAND_UP = "起立"
    HEAD_DOWN = "低头"
    NORMAL = "正常"


@dataclass
class PoseResult:
    pose_type: str
    confidence: float
    keypoint_info: Dict
    timestamp: float


class PoseEstimator:
    def __init__(self, config: dict = None):
        self.config = config or self._default_config()
        self._init_thresholds()
    
    def _default_config(self) -> dict:
        return {
            "standing_threshold": 5,
            "walking_distance_threshold": 30,
            "writing_height_threshold": 150,
            "facing_student_angle_threshold": 45,
            "hand_raise_threshold": 50,
            "head_drop_threshold": 30,
            "stand_up_threshold": 80
        }
    
    def _init_thresholds(self):
        self.standing_threshold = self.config.get("standing_threshold", 5)
        self.walking_distance_threshold = self.config.get("walking_distance_threshold", 30)
        self.writing_height_threshold = self.config.get("writing_height_threshold", 150)
        self.facing_student_angle_threshold = self.config.get("facing_student_angle_threshold", 45)
        self.hand_raise_threshold = self.config.get("hand_raise_threshold", 50)
        self.head_drop_threshold = self.config.get("head_drop_threshold", 30)
        self.stand_up_threshold = self.config.get("stand_up_threshold", 80)
    
    def estimate_teacher_pose(self, detection, frame_shape: Tuple[int, int]) -> PoseResult:
        if detection.keypoints is None:
            return PoseResult(
                pose_type=TeacherPose.UNKNOWN.value,
                confidence=0.0,
                keypoint_info={},
                timestamp=0.0
            )
        
        kps = detection.keypoints
        h, w = frame_shape
        
        nose = kps[0] if kps[0][0] > 0 else None
        left_shoulder = kps[5] if kps[5][0] > 0 else None
        right_shoulder = kps[6] if kps[6][0] > 0 else None
        left_wrist = kps[8] if kps[8][0] > 0 else None
        right_wrist = kps[9] if kps[9][0] > 0 else None
        left_hip = kps[11] if kps[11][0] > 0 else None
        right_hip = kps[12] if kps[12][0] > 0 else None
        
        pose_type, confidence = self._classify_teacher_pose(
            nose, left_shoulder, right_shoulder, 
            left_wrist, right_wrist, left_hip, right_hip,
            w, h
        )
        
        keypoint_info = {
            "nose": nose.tolist() if nose is not None else None,
            "left_shoulder": left_shoulder.tolist() if left_shoulder is not None else None,
            "right_shoulder": right_shoulder.tolist() if right_shoulder is not None else None,
            "left_wrist": left_wrist.tolist() if left_wrist is not None else None,
            "right_wrist": right_wrist.tolist() if right_wrist is not None else None,
            "left_hip": left_hip.tolist() if left_hip is not None else None,
            "right_hip": right_hip.tolist() if right_hip is not None else None
        }
        
        return PoseResult(
            pose_type=pose_type,
            confidence=confidence,
            keypoint_info=keypoint_info,
            timestamp=0.0
        )
    
    def _classify_teacher_pose(self, nose, left_shoulder, right_shoulder,
                               left_wrist, right_wrist, left_hip, right_hip,
                               frame_w: int, frame_h: int) -> Tuple[str, float]:
        if nose is None or left_shoulder is None or right_shoulder is None or left_hip is None or right_hip is None:
            return TeacherPose.UNKNOWN.value, 0.0
        
        shoulder_center = (left_shoulder + right_shoulder) / 2
        hip_center = (left_hip + right_hip) / 2
        torso_height = np.abs(hip_center[1] - shoulder_center[1]) * frame_h
        
        is_writing = False
        if left_wrist is not None and right_wrist is not None:
            avg_wrist_y = (left_wrist[1] + right_wrist[1]) / 2
            if shoulder_center[1] > avg_wrist_y:
                wrist_above_shoulder = (shoulder_center[1] - avg_wrist_y) * frame_h
                if wrist_above_shoulder > self.writing_height_threshold:
                    is_writing = True
        
        if is_writing:
            return TeacherPose.WRITING.value, 0.85
        
        if left_wrist is not None and right_wrist is not None:
            wrist_distance = np.sqrt(
                (left_wrist[0] - right_wrist[0])**2 + 
                (left_wrist[1] - right_wrist[1])**2
            ) * frame_w
            
            if wrist_distance < 0.15:
                return TeacherPose.STANDING.value, 0.75
        
        nose_to_shoulder = nose[1] - shoulder_center[1]
        if abs(nose_to_shoulder * frame_h) < self.standing_threshold:
            return TeacherPose.STANDING.value, 0.70
        
        return TeacherPose.WALKING.value, 0.65
    
    def estimate_student_behavior(self, detection, frame_shape: Tuple[int, int]) -> PoseResult:
        if detection.keypoints is None:
            return PoseResult(
                pose_type=StudentBehavior.NORMAL.value,
                confidence=0.0,
                keypoint_info={},
                timestamp=0.0
            )
        
        kps = detection.keypoints
        h, w = frame_shape
        
        nose = kps[0] if kps[0][0] > 0 else None
        left_shoulder = kps[5] if kps[5][0] > 0 else None
        right_shoulder = kps[6] if kps[6][0] > 0 else None
        left_wrist = kps[8] if kps[8][0] > 0 else None
        right_wrist = kps[9] if kps[9][0] > 0 else None
        left_hip = kps[11] if kps[11][0] > 0 else None
        right_hip = kps[12] if kps[12][0] > 0 else None
        
        behavior_type, confidence = self._classify_student_behavior(
            nose, left_shoulder, right_shoulder,
            left_wrist, right_wrist, left_hip, right_hip,
            w, h
        )
        
        keypoint_info = {
            "nose": nose.tolist() if nose is not None else None,
            "left_shoulder": left_shoulder.tolist() if left_shoulder is not None else None,
            "right_shoulder": right_shoulder.tolist() if right_shoulder is not None else None,
            "left_wrist": left_wrist.tolist() if left_wrist is not None else None,
            "right_wrist": right_wrist.tolist() if right_wrist is not None else None,
            "left_hip": left_hip.tolist() if left_hip is not None else None,
            "right_hip": right_hip.tolist() if right_hip is not None else None
        }
        
        return PoseResult(
            pose_type=behavior_type,
            confidence=confidence,
            keypoint_info=keypoint_info,
            timestamp=0.0
        )
    
    def _classify_student_behavior(self, nose, left_shoulder, right_shoulder,
                                   left_wrist, right_wrist, left_hip, right_hip,
                                   frame_w: int, frame_h: int) -> Tuple[str, float]:
        if not (left_shoulder and right_shoulder):
            return StudentBehavior.NORMAL.value, 0.0
        
        shoulder_center = (left_shoulder + right_shoulder) / 2
        
        hand_raised = False
        if left_wrist is not None:
            if left_wrist[1] < (shoulder_center[1] - 0.05):
                hand_raised = True
        if right_wrist is not None and not hand_raised:
            if right_wrist[1] < (shoulder_center[1] - 0.05):
                hand_raised = True
        
        if hand_raised:
            return StudentBehavior.HAND_RAISE.value, 0.80
        
        if left_hip is not None and right_hip is not None and nose is not None:
            hip_y = (left_hip[1] + right_hip[1]) / 2
            body_height = (hip_y - shoulder_center[1]) * frame_h
            
            if body_height > self.stand_up_threshold:
                return StudentBehavior.STAND_UP.value, 0.75
        
        if nose and shoulder_center:
            head_drop = (shoulder_center[1] - nose[1]) * frame_h
            if head_drop > self.head_drop_threshold:
                return StudentBehavior.HEAD_DOWN.value, 0.70
        
        return StudentBehavior.NORMAL.value, 0.60
    
    @staticmethod
    def get_pose_centroid(detection, frame_shape: Tuple[int, int]) -> Optional[Tuple[float, float]]:
        if detection.keypoints is None:
            return None
        
        kps = detection.keypoints
        valid_kps = [kp for kp in kps if kp[0] > 0]
        
        if not valid_kps:
            return None
        
        centroid = np.mean(valid_kps, axis=0)
        return (centroid[0] * frame_shape[1], centroid[1] * frame_shape[0])
    
    @staticmethod
    def get_box_center(box: np.ndarray) -> Tuple[float, float]:
        x_center = (box[0] + box[2]) / 2
        y_center = (box[1] + box[3]) / 2
        return (x_center, y_center)
    
    def update_config(self, config: dict):
        self.config.update(config)
        self._init_thresholds()
    
    def __repr__(self):
        return f"PoseEstimator(standing={self.standing_threshold}, walking={self.walking_distance_threshold})"