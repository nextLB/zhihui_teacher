import yaml
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MODEL_DIR = BASE_DIR / "models"
CONFIG_DIR = BASE_DIR / "config"

class Config:
    def __init__(self):
        self.model_name = "yolov8s-pose.pt"
        self.model_path = MODEL_DIR / self.model_name
        
        self.confidence_threshold = 0.5
        self.iou_threshold = 0.45
        
        self.video_source = 0
        self.video_fps = 30
        self.frame_skip = 1
        
        self.teacher_class_id = 0
        self.student_class_id = 0
        
        self.keypoint_threshold = 0.3
        
        self.standing_threshold = 5
        self.walking_distance_threshold = 30
        self.writing_height_threshold = 150
        self.facing_student_angle_threshold = 45
        
        self.hand_raise_threshold = 50
        self.head_drop_threshold = 30
        self.stand_up_threshold = 80
        
        self.interaction_distance_threshold = 200
        self.time_window = 60
        
        self.output_video = True
        self.output_json = True
        self.output_visualization = True
        
        self.classes = {
            "teacher_poses": ["站立", "走动", "板书", "面向学生"],
            "student_behaviors": ["举手", "起立", "低头", "正常"]
        }
        
    def to_dict(self):
        return {
            "model": {
                "name": self.model_name,
                "path": str(self.model_path),
                "confidence": self.confidence_threshold,
                "iou": self.iou_threshold,
                "keypoint_threshold": self.keypoint_threshold
            },
            "video": {
                "source": self.video_source,
                "fps": self.video_fps,
                "frame_skip": self.frame_skip
            },
            "detection": {
                "teacher_poses": self.classes["teacher_poses"],
                "student_behaviors": self.classes["student_behaviors"],
                "standing_threshold": self.standing_threshold,
                "walking_distance_threshold": self.walking_distance_threshold,
                "writing_height_threshold": self.writing_height_threshold,
                "facing_student_angle_threshold": self.facing_student_angle_threshold,
                "hand_raise_threshold": self.hand_raise_threshold,
                "head_drop_threshold": self.head_drop_threshold,
                "stand_up_threshold": self.stand_up_threshold
            },
            "statistics": {
                "interaction_distance_threshold": self.interaction_distance_threshold,
                "time_window": self.time_window
            },
            "output": {
                "video": self.output_video,
                "json": self.output_json,
                "visualization": self.output_visualization
            }
        }
    
    def save(self, path):
        with open(path, 'w', encoding='utf-8') as f:
            yaml.dump(self.to_dict(), f, allow_unicode=True, default_flow_style=False)
    
    @staticmethod
    def load(path):
        with open(path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        config = Config()
        config.model_name = data["model"]["name"]
        config.confidence_threshold = data["model"]["confidence"]
        config.iou_threshold = data["model"]["iou"]
        config.keypoint_threshold = data["model"]["keypoint_threshold"]
        config.video_source = data["video"]["source"]
        config.video_fps = data["video"]["fps"]
        config.frame_skip = data["video"]["frame_skip"]
        return config

config = Config()