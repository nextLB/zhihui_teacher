import cv2
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class Visualizer:
    POSE_COLORS = {
        "Standing": (0, 255, 0),
        "Walking": (255, 165, 0),
        "Writing": (0, 165, 255),
        "Facing Student": (255, 0, 255)
    }
    
    BEHAVIOR_COLORS = {
        "Hand Raise": (0, 255, 255),
        "Stand Up": (0, 255, 0),
        "Head Down": (128, 128, 128),
        "Normal": (255, 255, 255)
    }
    
    POSE_LABELS = {
        "站立": "Standing",
        "走动": "Walking",
        "板书": "Writing",
        "面向学生": "Facing Student"
    }
    
    BEHAVIOR_LABELS = {
        "举手": "Hand Raise",
        "起立": "Stand Up",
        "低头": "Head Down",
        "正常": "Normal"
    }
    
    KEYPOINT_CONNECTIONS = [
        (0, 1), (0, 2), (1, 3), (2, 4),
        (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
        (5, 11), (6, 12), (11, 12),
        (11, 13), (13, 15), (12, 14), (14, 16)
    ]
    
    def __init__(self, show_labels: bool = True, show_keypoints: bool = True):
        self.show_labels = show_labels
        self.show_keypoints = show_keypoints
        self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.font_thickness = 2
    
    def draw_detection(self, frame: np.ndarray, detection, pose_type: str = None,
                      behavior_type: str = None, label: str = "person") -> np.ndarray:
        if detection is None:
            return frame
        
        box = detection.box
        x1, y1, x2, y2 = int(box[0]), int(box[1]), int(box[2]), int(box[3])
        
        if pose_type and pose_type in self.POSE_COLORS:
            color = self.POSE_COLORS[pose_type]
        elif behavior_type and behavior_type in self.BEHAVIOR_COLORS:
            color = self.BEHAVIOR_COLORS[behavior_type]
        else:
            color = (0, 255, 0)
        
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        
        if self.show_labels:
            label_text = f"{label}"
            display_pose = self.POSE_LABELS.get(pose_type, pose_type) if pose_type else None
            display_behavior = self.BEHAVIOR_LABELS.get(behavior_type, behavior_type) if behavior_type else None
            if display_pose:
                label_text = f"{label}: {display_pose}"
            elif display_behavior:
                label_text = f"{label}: {display_behavior}"
            
            confidence = detection.confidence
            label_text = f"{label_text} {confidence:.2f}"
            
            (text_width, text_height), baseline = cv2.getTextSize(
                label_text, self.font, self.font_scale, self.font_thickness
            )
            
            cv2.rectangle(frame, (x1, y1 - text_height - 10), 
                         (x1 + text_width, y1), color, -1)
            
            cv2.putText(frame, label_text, (x1, y1 - 5),
                       self.font, self.font_scale, (255, 255, 255), self.font_thickness)
        
        return frame
    
    def draw_keypoints(self, frame: np.ndarray, keypoints: np.ndarray,
                      keypoint_scores: np.ndarray = None, threshold: float = 0.3) -> np.ndarray:
        if keypoints is None:
            return frame
        
        h, w = frame.shape[:2]
        
        for i, kp in enumerate(keypoints):
            if kp[0] <= 0 or kp[1] <= 0:
                continue
            
            if keypoint_scores is not None and keypoint_scores[i] < threshold:
                continue
            
            x = int(kp[0] * w)
            y = int(kp[1] * h)
            
            cv2.circle(frame, (x, y), 4, (0, 255, 255), -1)
        
        for connection in self.KEYPOINT_CONNECTIONS:
            if connection[0] >= len(keypoints) or connection[1] >= len(keypoints):
                continue
            
            kp1 = keypoints[connection[0]]
            kp2 = keypoints[connection[1]]
            
            if kp1[0] <= 0 or kp1[1] <= 0 or kp2[0] <= 0 or kp2[1] <= 0:
                continue
            
            if keypoint_scores is not None:
                if keypoint_scores[connection[0]] < threshold or keypoint_scores[connection[1]] < threshold:
                    continue
            
            x1 = int(kp1[0] * w)
            y1 = int(kp1[1] * h)
            x2 = int(kp2[0] * w)
            y2 = int(kp2[1] * h)
            
            cv2.line(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        
        return frame
    
    def draw_info(self, frame: np.ndarray, info: Dict, position: Tuple[int, int] = (10, 30)) -> np.ndarray:
        y_offset = position[1]
        
        for key, value in info.items():
            text = f"{key}: {value}"
            cv2.putText(frame, text, (position[0], y_offset),
                       self.font, 0.5, (255, 255, 255), 1)
            y_offset += 20
        
        return frame
    
    def draw_statistics(self, frame: np.ndarray, statistics: Dict,
                       position: Tuple[int, int] = (10, 30)) -> np.ndarray:
        y_offset = position[1]
        
        cv2.rectangle(frame, (5, 5), (300, 200), (0, 0, 0), -1)
        cv2.rectangle(frame, (5, 5), (300, 200), (255, 255, 255), 1)
        
        for key, value in statistics.items():
            if isinstance(value, float):
                text = f"{key}: {value:.2f}"
            else:
                text = f"{key}: {value}"
            
            cv2.putText(frame, text, (15, y_offset),
                       self.font, 0.5, (0, 255, 0), 1)
            y_offset += 18
        
        return frame
    
    def create_summary_image(self, statistics: Dict, features: Dict = None,
                            size: Tuple[int, int] = (800, 600)) -> np.ndarray:
        canvas = np.ones((size[1], size[0], 3), dtype=np.uint8) * 255
        
        title = "Classroom Behavior Analysis Report"
        cv2.putText(canvas, title, (250, 40),
                   self.font, 1.0, (0, 0, 0), 2)
        
        y_pos = 80
        
        cv2.putText(canvas, "Teacher Pose Distribution:", (50, y_pos),
                   self.font, 0.7, (0, 0, 0), 1)
        y_pos += 30
        
        pose_ratios = statistics.get("teacher_pose_time_ratio", {})
        for pose, ratio in pose_ratios.items():
            display_pose = self.POSE_LABELS.get(pose, pose)
            text = f"  {display_pose}: {ratio*100:.1f}%"
            cv2.putText(canvas, text, (70, y_pos),
                       self.font, 0.6, (0, 0, 0), 1)
            y_pos += 22
        
        y_pos += 20
        cv2.putText(canvas, "Student Behavior Stats:", (50, y_pos),
                   self.font, 0.7, (0, 0, 0), 1)
        y_pos += 30
        
        behavior_counts = statistics.get("student_behavior_counts", {})
        for behavior, count in behavior_counts.items():
            display_behavior = self.BEHAVIOR_LABELS.get(behavior, behavior)
            text = f"  {display_behavior}: {count}"
            cv2.putText(canvas, text, (70, y_pos),
                       self.font, 0.6, (0, 0, 0), 1)
            y_pos += 22
        
        y_pos += 20
        cv2.putText(canvas, "Classroom Interaction:", (50, y_pos),
                   self.font, 0.7, (0, 0, 0), 1)
        y_pos += 30
        
        interaction_count = statistics.get("interaction_count", 0)
        interaction_freq = statistics.get("interaction_frequency", 0)
        walking_range = statistics.get("walking_range", 0)
        
        text = f"  Interactions: {interaction_count}"
        cv2.putText(canvas, text, (70, y_pos),
                   self.font, 0.6, (0, 0, 0), 1)
        y_pos += 22
        
        text = f"  Frequency: {interaction_freq:.2f}/s"
        cv2.putText(canvas, text, (70, y_pos),
                   self.font, 0.6, (0, 0, 0), 1)
        y_pos += 22
        
        text = f"  Walking Range: {walking_range:.1f}px"
        cv2.putText(canvas, text, (70, y_pos),
                   self.font, 0.6, (0, 0, 0), 1)
        
        if features:
            y_pos += 40
            cv2.putText(canvas, "Behavior Features:", (50, y_pos),
                       self.font, 0.7, (0, 0, 0), 1)
            y_pos += 30
            
            engagement = features.get("engagement_score", 0)
            attention = features.get("attention_score", 0)
            
            text = f"  Engagement Score: {engagement:.2f}"
            cv2.putText(canvas, text, (70, y_pos),
                       self.font, 0.6, (0, 0, 0), 1)
            y_pos += 22
            
            text = f"  Attention Score: {attention:.2f}"
            cv2.putText(canvas, text, (70, y_pos),
                       self.font, 0.6, (0, 0, 0), 1)
        
        return canvas
    
    def create_timeline_chart(self, pose_history: List[Dict], 
                             behavior_history: List[Dict] = None,
                             width: int = 800, height: int = 200) -> np.ndarray:
        canvas = np.ones((height, width, 3), dtype=np.uint8) * 240
        
        if not pose_history:
            return canvas
        
        cv2.putText(canvas, "Teacher Pose Timeline", (20, 25),
                   self.font, 0.7, (0, 0, 0), 1)
        
        times = [p["timestamp"] for p in pose_history]
        min_time = min(times) if times else 0
        max_time = max(times) if times else 1
        
        if max_time - min_time < 0.001:
            max_time = min_time + 1
        
        pose_colors = {
            "Standing": (0, 255, 0),
            "Walking": (255, 165, 0),
            "Writing": (0, 165, 255),
            "Facing Student": (255, 0, 255),
            "Unknown": (128, 128, 128)
        }
        
        y_base = height - 30
        
        for i in range(len(pose_history) - 1):
            x1 = int((pose_history[i]["timestamp"] - min_time) / (max_time - min_time) * (width - 100)) + 50
            x2 = int((pose_history[i+1]["timestamp"] - min_time) / (max_time - min_time) * (width - 100)) + 50
            
            pose = pose_history[i]["pose"]
            color = pose_colors.get(pose, (128, 128, 128))
            
            cv2.line(canvas, (x1, y_base - 20), (x2, y_base - 20), color, 8)
        
        for pose, color in pose_colors.items():
            legend_y = 40
            cv2.line(canvas, (20, legend_y), (40, legend_y), color, 8)
            cv2.putText(canvas, pose, (50, legend_y + 5),
                       self.font, 0.5, (0, 0, 0), 1)
        
        return canvas
    
    def save_visualization(self, frame: np.ndarray, output_path: str):
        cv2.imwrite(output_path, frame)
        logger.info(f"可视化图像已保存: {output_path}")
    
    def create_grid_visualization(self, frames: List[np.ndarray], 
                                  labels: List[str] = None,
                                  grid_size: Tuple[int, int] = None) -> np.ndarray:
        if not frames:
            return np.zeros((480, 640, 3), dtype=np.uint8)
        
        if grid_size is None:
            cols = min(len(frames), 3)
            rows = (len(frames) + cols - 1) // cols
        else:
            rows, cols = grid_size
        
        h, w = frames[0].shape[:2]
        
        canvas = np.ones((rows * h, cols * w, 3), dtype=np.uint8) * 255
        
        for idx, frame in enumerate(frames):
            if idx >= rows * cols:
                break
            
            row = idx // cols
            col = idx % cols
            
            if frame.shape[:2] != (h, w):
                frame = cv2.resize(frame, (w, h))
            
            canvas[row*h:(row+1)*h, col*w:(col+1)*w] = frame
            
            if labels and idx < len(labels):
                cv2.putText(canvas, labels[idx], (col*w + 10, row*h + 30),
                           self.font, 0.6, (255, 255, 255), 2)
        
        return canvas
    
    def __repr__(self):
        return f"Visualizer(show_labels={self.show_labels}, show_keypoints={self.show_keypoints})"