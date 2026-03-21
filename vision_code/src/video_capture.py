import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Generator
import logging

logger = logging.getLogger(__name__)


class VideoCapture:
    def __init__(self, source: int | str = 0):
        self.source = source
        self.cap: Optional[cv2.VideoCapture] = None
        self.frame_count = 0
        self.fps = 0
        self.width = 0
        self.height = 0
        self.total_frames = 0
        
    def open(self) -> bool:
        if isinstance(self.source, int):
            self.cap = cv2.VideoCapture(self.source)
            if not self.cap.isOpened():
                logger.error(f"无法打开摄像头 {self.source}")
                return False
        elif isinstance(self.source, str):
            video_path = Path(self.source)
            if not video_path.exists():
                logger.error(f"视频文件不存在: {self.source}")
                return False
            self.cap = cv2.VideoCapture(str(video_path))
            if not self.cap.isOpened():
                logger.error(f"无法打开视频文件: {self.source}")
                return False
        else:
            logger.error(f"无效的视频源: {self.source}")
            return False
        
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frame_count = 0
        
        logger.info(f"视频源打开成功: {self.width}x{self.height} @ {self.fps}fps, 共{self.total_frames}帧")
        return True
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if self.cap is None:
            return False, None
        
        ret, frame = self.cap.read()
        if ret:
            self.frame_count += 1
        return ret, frame
    
    def read_frame(self, frame_number: int) -> Tuple[bool, Optional[np.ndarray]]:
        if self.cap is None:
            return False, None
        
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
        return self.read()
    
    def stream(self, skip_frames: int = 1) -> Generator[Tuple[int, np.ndarray], None, None]:
        if self.cap is None:
            return
        
        frame_idx = 0
        while True:
            ret, frame = self.read()
            if not ret:
                break
            
            if frame_idx % (skip_frames + 1) == 0:
                yield self.frame_count - 1, frame
            
            frame_idx += 1
    
    def get_position(self) -> Tuple[int, float]:
        if self.cap is None:
            return 0, 0.0
        frame_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
        time_sec = self.cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
        return int(frame_pos), time_sec
    
    def seek(self, frame_number: int) -> bool:
        if self.cap is None:
            return False
        return self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
    
    def reset(self) -> bool:
        if self.cap is None:
            return False
        return self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
    
    def get_info(self) -> dict:
        return {
            "source": self.source,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "total_frames": self.total_frames,
            "current_frame": self.frame_count
        }
    
    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
            logger.info("视频源已关闭")
    
    def __enter__(self):
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


class VideoWriter:
    def __init__(self, output_path: str, fps: float = 30.0, frame_size: Tuple[int, int] = None):
        self.output_path = output_path
        self.fps = fps
        self.frame_size = frame_size
        self.writer: Optional[cv2.VideoWriter] = None
        self.frame_count = 0
    
    def open(self, frame_size: Tuple[int, int]):
        self.frame_size = frame_size
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(
            self.output_path,
            fourcc,
            self.fps,
            self.frame_size
        )
        if not self.writer.isOpened():
            logger.error(f"无法创建视频写入器: {self.output_path}")
            return False
        logger.info(f"视频写入器已创建: {self.output_path}")
        return True
    
    def write(self, frame: np.ndarray):
        if self.writer is None:
            return
        self.writer.write(frame)
        self.frame_count += 1
    
    def release(self):
        if self.writer is not None:
            self.writer.release()
            self.writer = None
            logger.info(f"视频已保存: {self.output_path}, 共{self.frame_count}帧")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


def save_frame(frame: np.ndarray, output_path: str):
    cv2.imwrite(output_path, frame)
    logger.info(f"帧已保存: {output_path}")


def load_video_info(video_path: str) -> dict:
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        return {}
    
    info = {
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "fps": cap.get(cv2.CAP_PROP_FPS),
        "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS)
    }
    cap.release()
    return info