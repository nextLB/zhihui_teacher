import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Detection:
    box: np.ndarray
    confidence: float
    class_id: int
    class_name: str
    keypoints: Optional[np.ndarray] = None
    keypoint_scores: Optional[np.ndarray] = None


class PoseDetector:
    COCO_KEYPOINTS = [
        'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
        'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist',
        'left_hip', 'right_hip',
        'left_knee', 'right_knee',
        'left_ankle', 'right_ankle'
    ]
    
    def __init__(self, model_path: str = "yolov8s-pose.pt", confidence: float = 0.5, 
                 iou_threshold: float = 0.45, keypoint_threshold: float = 0.3):
        self.model_path = model_path
        self.confidence = confidence
        self.iou_threshold = iou_threshold
        self.keypoint_threshold = keypoint_threshold
        self.model = None
        self._load_model()
    
    def _load_model(self):
        try:
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            logger.info(f"模型加载成功: {self.model_path}")
        except Exception as e:
            logger.error(f"模型加载失败: {e}")
            raise
    
    def detect(self, frame: np.ndarray, verbose: bool = False) -> List[Detection]:
        if self.model is None:
            return []
        
        results = self.model(frame, conf=self.confidence, iou=self.iou_threshold, verbose=verbose)
        
        detections = []
        if results and len(results) > 0:
            result = results[0]
            
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                for i in range(len(boxes)):
                    detection = Detection(
                        box=boxes[i],
                        confidence=confidences[i],
                        class_id=class_ids[i],
                        class_name="person"
                    )
                    detections.append(detection)
            
            if (result.keypoints is not None and len(result.keypoints) > 0 and 
                result.keypoints.xyn is not None):
                keypoints = result.keypoints.xyn.cpu().numpy()
                keypoint_scores = None
                if result.keypoints.conf is not None:
                    keypoint_scores = result.keypoints.conf.cpu().numpy()
                
                keypoint_count = min(len(detections), len(keypoints))
                for i in range(keypoint_count):
                    detections[i].keypoints = keypoints[i]
                    if keypoint_scores is not None:
                        detections[i].keypoint_scores = keypoint_scores[i]
        
        return detections
    
    def detect_batch(self, frames: List[np.ndarray]) -> List[List[Detection]]:
        if self.model is None:
            return [[] for _ in frames]
        
        results = self.model(frames, conf=self.confidence, iou=self.iou_threshold)
        
        all_detections = []
        for result in results:
            detections = []
            if result.boxes is not None and len(result.boxes) > 0:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                class_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                for i in range(len(boxes)):
                    detection = Detection(
                        box=boxes[i],
                        confidence=confidences[i],
                        class_id=class_ids[i],
                        class_name="person"
                    )
                    detections.append(detection)
            
            if (result.keypoints is not None and len(result.keypoints) > 0 and 
                result.keypoints.xyn is not None):
                keypoints = result.keypoints.xyn.cpu().numpy()
                keypoint_scores = None
                if result.keypoints.conf is not None:
                    keypoint_scores = result.keypoints.conf.cpu().numpy()
                
                keypoint_count = min(len(detections), len(keypoints))
                for i in range(keypoint_count):
                    detections[i].keypoints = keypoints[i]
                    if keypoint_scores is not None:
                        detections[i].keypoint_scores = keypoint_scores[i]
            
            all_detections.append(detections)
        
        return all_detections
    
    @staticmethod
    def get_keypoint(detection: Detection, name: str) -> Optional[Tuple[float, float, float]]:
        if detection.keypoints is None:
            return None
        
        idx = PoseDetector.COCO_KEYPOINTS.index(name) if name in PoseDetector.COCO_KEYPOINTS else -1
        if idx == -1 or idx >= len(detection.keypoints):
            return None
        
        kp = detection.keypoints[idx]
        score = detection.keypoint_scores[idx] if detection.keypoint_scores is not None else 0
        
        if score >= 0.3:
            return (kp[0], kp[1], score)
        return None
    
    @staticmethod
    def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)
    
    @staticmethod
    def calculate_angle(p1: Tuple[float, float], p2: Tuple[float, float], p3: Tuple[float, float]) -> float:
        v1 = np.array([p1[0] - p2[0], p1[1] - p2[1]])
        v2 = np.array([p3[0] - p2[0], p3[1] - p2[1]])
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
        cos_angle = np.clip(cos_angle, -1, 1)
        angle = np.arccos(cos_angle) * 180 / np.pi
        
        return angle
    
    @staticmethod
    def box_area(box: np.ndarray) -> float:
        return (box[2] - box[0]) * (box[3] - box[1])
    
    @staticmethod
    def iou(box1: np.ndarray, box2: np.ndarray) -> float:
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        
        area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
        area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
        
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0
    
    @staticmethod
    def non_max_suppression(detections: List[Detection], iou_threshold: float = 0.45) -> List[Detection]:
        if not detections:
            return []
        
        boxes = np.array([d.box for d in detections])
        scores = np.array([d.confidence for d in detections])
        
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        
        areas = (x2 - x1) * (y2 - y1)
        order = scores.argsort()[::-1]
        
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            
            if order.size == 1:
                break
            
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])
            
            w = np.maximum(0, xx2 - xx1)
            h = np.maximum(0, yy2 - yy1)
            
            intersection = w * h
            union = areas[i] + areas[order[1:]] - intersection
            iou = intersection / (union + 1e-8)
            
            inds = np.where(iou <= iou_threshold)[0]
            order = order[inds + 1]
        
        return [detections[i] for i in keep]
    
    def get_pose_info(self, detection: Detection) -> Dict:
        info = {
            "has_keypoints": detection.keypoints is not None,
            "keypoint_count": len(detection.keypoints) if detection.keypoints is not None else 0,
            "keypoints": {}
        }
        
        for kp_name in self.COCO_KEYPOINTS:
            kp = self.get_keypoint(detection, kp_name)
            if kp:
                info["keypoints"][kp_name] = {"x": kp[0], "y": kp[1], "score": kp[2]}
        
        return info
    
    def __repr__(self):
        return f"PoseDetector(model={self.model_path}, conf={self.confidence}, iou={self.iou_threshold})"