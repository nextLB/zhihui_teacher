import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class TimeSegment:
    start_time: float
    end_time: float
    duration: float
    pose_type: str
    frame_start: int
    frame_end: int


@dataclass
class InteractionEvent:
    timestamp: float
    frame_id: int
    teacher_id: int
    student_id: int
    distance: float
    duration: float = 0.0


class ClassroomStatistics:
    def __init__(self, config: dict = None):
        self.config = config or {}
        
        self.teacher_pose_segments: List[TimeSegment] = []
        self.current_teacher_pose: Optional[str] = None
        self.current_pose_start_time: float = 0.0
        self.current_pose_start_frame: int = 0
        
        self.student_behavior_events: List[Dict] = []
        self.interaction_events: List[InteractionEvent] = []
        
        self.teacher_positions: List[Tuple[float, float, float]] = []
        
        self.total_frames = 0
        self.total_duration = 0.0
        
        self._pose_timeaccumulator: Dict[str, float] = defaultdict(float)
        self._behavior_count: Dict[str, int] = defaultdict(int)
    
    def start_pose_tracking(self, pose_type: str, timestamp: float, frame_id: int):
        if self.current_teacher_pose is not None:
            self._finish_current_pose(timestamp, frame_id)
        
        self.current_teacher_pose = pose_type
        self.current_pose_start_time = timestamp
        self.current_pose_start_frame = frame_id
    
    def _finish_current_pose(self, end_time: float, end_frame: int):
        if self.current_teacher_pose is None:
            return
        
        duration = end_time - self.current_pose_start_time
        segment = TimeSegment(
            start_time=self.current_pose_start_time,
            end_time=end_time,
            duration=duration,
            pose_type=self.current_teacher_pose,
            frame_start=self.current_pose_start_frame,
            frame_end=end_frame
        )
        self.teacher_pose_segments.append(segment)
        self._pose_timeaccumulator[self.current_teacher_pose] += duration
    
    def finish_pose_tracking(self, timestamp: float, frame_id: int):
        if self.current_teacher_pose is not None:
            self._finish_current_pose(timestamp, frame_id)
            self.current_teacher_pose = None
    
    def add_student_behavior(self, behavior: str, timestamp: float, frame_id: int):
        event = {
            "behavior": behavior,
            "timestamp": timestamp,
            "frame_id": frame_id
        }
        self.student_behavior_events.append(event)
        self._behavior_count[behavior] += 1
    
    def add_interaction(self, teacher_id: int, student_id: int, distance: float,
                       timestamp: float, frame_id: int):
        event = InteractionEvent(
            timestamp=timestamp,
            frame_id=frame_id,
            teacher_id=teacher_id,
            student_id=student_id,
            distance=distance
        )
        self.interaction_events.append(event)
    
    def add_teacher_position(self, x: float, y: float, timestamp: float):
        self.teacher_positions.append((x, y, timestamp))
    
    def update_progress(self, frame_count: int, duration: float):
        self.total_frames = frame_count
        self.total_duration = duration
    
    def get_teacher_pose_time_ratio(self) -> Dict[str, float]:
        if self.total_duration <= 0:
            return {}
        
        return {
            pose: time / self.total_duration 
            for pose, time in self._pose_timeaccumulator.items()
        }
    
    def get_student_behavior_counts(self) -> Dict[str, int]:
        return dict(self._behavior_count)
    
    def get_interaction_count(self) -> int:
        return len(self.interaction_events)
    
    def get_interaction_frequency(self) -> float:
        if self.total_duration <= 0:
            return 0.0
        return len(self.interaction_events) / self.total_duration
    
    def get_walking_range(self) -> float:
        if len(self.teacher_positions) < 2:
            return 0.0
        
        positions = np.array([(p[0], p[1]) for p in self.teacher_positions])
        
        x_range = positions[:, 0].max() - positions[:, 0].min()
        y_range = positions[:, 1].max() - positions[:, 1].min()
        
        return np.sqrt(x_range**2 + y_range**2)
    
    def get_walking_speed(self) -> float:
        if len(self.teacher_positions) < 2:
            return 0.0
        
        total_distance = 0.0
        for i in range(1, len(self.teacher_positions)):
            dx = self.teacher_positions[i][0] - self.teacher_positions[i-1][0]
            dy = self.teacher_positions[i][1] - self.teacher_positions[i-1][1]
            dt = self.teacher_positions[i][2] - self.teacher_positions[i-1][2]
            
            if dt > 0:
                distance = np.sqrt(dx**2 + dy**2)
                speed = distance / dt
                total_distance += speed
        
        avg_speed = total_distance / (len(self.teacher_positions) - 1) if len(self.teacher_positions) > 1 else 0
        return avg_speed
    
    def get_pose_transition_count(self) -> int:
        if len(self.teacher_pose_segments) < 2:
            return 0
        
        transitions = 0
        for i in range(1, len(self.teacher_pose_segments)):
            if self.teacher_pose_segments[i].pose_type != self.teacher_pose_segments[i-1].pose_type:
                transitions += 1
        
        return transitions
    
    def get_average_pose_duration(self) -> Dict[str, float]:
        pose_durations = defaultdict(list)
        
        for segment in self.teacher_pose_segments:
            pose_durations[segment.pose_type].append(segment.duration)
        
        return {
            pose: np.mean(durations) if durations else 0.0
            for pose, durations in pose_durations.items()
        }
    
    def get_interaction_duration_ratio(self) -> float:
        if self.total_duration <= 0:
            return 0.0
        
        total_interaction_time = 0.0
        current_interaction_start = None
        
        in_interaction = False
        
        sorted_events = sorted(self.interaction_events, key=lambda x: x.timestamp)
        
        for i, event in enumerate(sorted_events):
            if not in_interaction:
                current_interaction_start = event.timestamp
                in_interaction = True
            else:
                if event.timestamp - sorted_events[i-1].timestamp > 1.0:
                    total_interaction_time += event.timestamp - current_interaction_start
                    current_interaction_start = event.timestamp
        
        if in_interaction and current_interaction_start is not None:
            total_interaction_time += self.total_duration - current_interaction_start
        
        return total_interaction_time / self.total_duration if self.total_duration > 0 else 0.0
    
    def get_summary(self) -> Dict:
        return {
            "total_frames": self.total_frames,
            "total_duration": self.total_duration,
            "teacher_pose_time_ratio": self.get_teacher_pose_time_ratio(),
            "student_behavior_counts": self.get_student_behavior_counts(),
            "interaction_count": self.get_interaction_count(),
            "interaction_frequency": self.get_interaction_frequency(),
            "interaction_duration_ratio": self.get_interaction_duration_ratio(),
            "walking_range": self.get_walking_range(),
            "walking_speed": self.get_walking_speed(),
            "pose_transition_count": self.get_pose_transition_count(),
            "average_pose_duration": self.get_average_pose_duration()
        }
    
    def reset(self):
        self.teacher_pose_segments.clear()
        self.current_teacher_pose = None
        self.student_behavior_events.clear()
        self.interaction_events.clear()
        self.teacher_positions.clear()
        self.total_frames = 0
        self.total_duration = 0.0
        self._pose_timeaccumulator.clear()
        self._behavior_count.clear()
    
    def save(self, path: str):
        import json
        
        data = {
            "summary": self.get_summary(),
            "pose_segments": [
                {
                    "start_time": seg.start_time,
                    "end_time": seg.end_time,
                    "duration": seg.duration,
                    "pose_type": seg.pose_type,
                    "frame_start": seg.frame_start,
                    "frame_end": seg.frame_end
                }
                for seg in self.teacher_pose_segments
            ],
            "student_behaviors": self.student_behavior_events,
            "interactions": [
                {
                    "timestamp": evt.timestamp,
                    "frame_id": evt.frame_id,
                    "teacher_id": evt.teacher_id,
                    "student_id": evt.student_id,
                    "distance": evt.distance
                }
                for evt in self.interaction_events
            ]
        }
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"统计数据已保存: {path}")
    
    def load(self, path: str):
        import json
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.teacher_pose_segments = [
            TimeSegment(
                start_time=seg["start_time"],
                end_time=seg["end_time"],
                duration=seg["duration"],
                pose_type=seg["pose_type"],
                frame_start=seg["frame_start"],
                frame_end=seg["frame_end"]
            )
            for seg in data.get("pose_segments", [])
        ]
        
        self.student_behavior_events = data.get("student_behaviors", [])
        self.interaction_events = [
            InteractionEvent(
                timestamp=evt["timestamp"],
                frame_id=evt["frame_id"],
                teacher_id=evt["teacher_id"],
                student_id=evt["student_id"],
                distance=evt["distance"]
            )
            for evt in data.get("interactions", [])
        ]
        
        summary = data.get("summary", {})
        self.total_frames = summary.get("total_frames", 0)
        self.total_duration = summary.get("total_duration", 0.0)
        
        self._pose_timeaccumulator = defaultdict(float, summary.get("teacher_pose_time_ratio", {}))
        self._behavior_count = defaultdict(int, summary.get("student_behavior_counts", {}))
        
        logger.info(f"统计数据已加载: {path}")
    
    def __repr__(self):
        return f"ClassroomStatistics(frames={self.total_frames}, duration={self.total_duration:.1f}s)"