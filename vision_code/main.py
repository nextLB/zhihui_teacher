import argparse
import logging
import sys
import time
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent))

from src.video_capture import VideoCapture, VideoWriter
from src.detector import PoseDetector
from src.pose_estimator import PoseEstimator, TeacherPose, StudentBehavior
from src.behavior_recognizer import BehaviorRecognizer
from src.statistics import ClassroomStatistics
from src.feature_extractor import FeatureExtractor
from src.visualizer import Visualizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ClassroomAnalyzer:
    def __init__(self, args):
        self.args = args
        
        self.detector = None
        self.pose_estimator = None
        self.behavior_recognizer = None
        self.statistics = None
        self.feature_extractor = None
        self.visualizer = None
        
        self.output_writer = None
        self.current_pose = None
        
        self.frame_count = 0
        self.start_time = 0
        self.last_pose_update_time = 0
    
    def initialize(self):
        logger.info("初始化分析器...")
        
        self.detector = PoseDetector(
            model_path=self.args.model,
            confidence=self.args.confidence,
            iou_threshold=self.args.iou,
            keypoint_threshold=self.args.keypoint_threshold
        )
        
        self.pose_estimator = PoseEstimator({
            "standing_threshold": self.args.standing_threshold,
            "walking_distance_threshold": self.args.walking_distance,
            "writing_height_threshold": self.args.writing_height,
            "facing_student_angle_threshold": self.args.facing_angle,
            "hand_raise_threshold": self.args.hand_raise_threshold,
            "head_drop_threshold": self.args.head_drop_threshold,
            "stand_up_threshold": self.args.stand_up_threshold
        })
        
        self.behavior_recognizer = BehaviorRecognizer({
            "interaction_distance_threshold": self.args.interaction_distance,
            "time_window": self.args.time_window
        })
        
        self.statistics = ClassroomStatistics()
        self.feature_extractor = FeatureExtractor()
        self.feature_extractor.set_statistics(self.statistics)
        
        self.visualizer = Visualizer(
            show_labels=True,
            show_keypoints=True
        )
        
        logger.info("初始化完成")
    
    def process_frame(self, frame):
        frame_shape = (frame.shape[0], frame.shape[1])
        
        detections = self.detector.detect(frame)
        
        current_time = time.time() - self.start_time
        frame_analyses = self.behavior_recognizer.analyze_frame(
            detections, self.frame_count, current_time, frame_shape
        )
        
        for i, det in enumerate(detections):
            pose_type = None
            behavior_type = None
            
            if det.keypoints is not None:
                pose_result = self.pose_estimator.estimate_teacher_pose(det, frame_shape)
                pose_type = pose_result.pose_type
                
                if self.current_pose is None or self.current_pose != pose_type:
                    if self.current_pose is not None:
                        self.statistics.finish_pose_tracking(
                            current_time, self.frame_count
                        )
                    self.statistics.start_pose_tracking(
                        pose_type, current_time, self.frame_count
                    )
                    self.current_pose = pose_type
                    self.last_pose_update_time = current_time
                
                centroid = PoseEstimator.get_pose_centroid(det, frame_shape)
                if centroid:
                    self.statistics.add_teacher_position(
                        centroid[0], centroid[1], current_time
                    )
            else:
                behavior_result = self.pose_estimator.estimate_student_behavior(det, frame_shape)
                behavior_type = behavior_result.pose_type
                
                if behavior_type != StudentBehavior.NORMAL.value:
                    self.statistics.add_student_behavior(
                        behavior_type, current_time, self.frame_count
                    )
            
            if self.args.visualize:
                frame = self.visualizer.draw_detection(
                    frame, det, pose_type=pose_type, behavior_type=behavior_type
                )
                
                if det.keypoints is not None:
                    frame = self.visualizer.draw_keypoints(
                        frame, det.keypoints, det.keypoint_scores
                    )
        
        if self.args.show_stats:
            current_pose_en = self.current_pose
            if current_pose_en:
                from src.visualizer import Visualizer
                for cn, en in Visualizer.POSE_LABELS.items():
                    if cn == current_pose_en:
                        current_pose_en = en
                        break
            stats_info = {
                "Frame": self.frame_count,
                "Time": f"{current_time:.1f}s",
                "Detections": len(detections),
                "Current Pose": current_pose_en if current_pose_en else "None"
            }
            frame = self.visualizer.draw_statistics(frame, stats_info)
        
        return frame, detections
    
    def run_video(self, video_path: str):
        logger.info(f"开始分析视频: {video_path}")
        
        video_cap = VideoCapture(video_path)
        if not video_cap.open():
            logger.error("无法打开视频")
            return
        
        video_info = video_cap.get_info()
        logger.info(f"视频信息: {video_info}")
        
        if self.args.output_video:
            output_path = self.args.output.replace('.', '_output.')
            self.output_writer = VideoWriter(
                output_path,
                fps=video_info.get("fps", 30),
                frame_size=(video_info["width"], video_info["height"])
            )
            self.output_writer.open((video_info["width"], video_info["height"]))
        
        self.start_time = time.time()
        
        try:
            for frame_id, frame in video_cap.stream(skip_frames=self.args.skip_frames):
                processed_frame, detections = self.process_frame(frame)
                
                if self.output_writer:
                    self.output_writer.write(processed_frame)
                
                if self.args.display:
                    cv2.imshow("Classroom Analysis", processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if frame_id % 100 == 0:
                    logger.info(f"已处理 {frame_id} 帧")
                
                self.frame_count = frame_id
                
        except KeyboardInterrupt:
            logger.info("用户中断")
        finally:
            video_cap.release()
            if self.output_writer:
                self.output_writer.release()
            if self.args.display:
                cv2.destroyAllWindows()
        
        self._save_results()
        
        duration = time.time() - self.start_time
        logger.info(f"分析完成, 耗时: {duration:.1f}s")
    
    def run_camera(self, camera_id: int = 0):
        logger.info(f"开始摄像头捕获: {camera_id}")
        
        video_cap = VideoCapture(camera_id)
        if not video_cap.open():
            logger.error("无法打开摄像头")
            return
        
        if self.args.display:
            cv2.namedWindow("Classroom Analysis")
        
        self.start_time = time.time()
        
        try:
            while True:
                ret, frame = video_cap.read()
                if not ret:
                    break
                
                processed_frame, detections = self.process_frame(frame)
                
                if self.args.display:
                    cv2.imshow("Classroom Analysis", processed_frame)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                
                if self.frame_count % 30 == 0:
                    logger.info(f"已处理 {self.frame_count} 帧")
                
                self.frame_count += 1
                
        except KeyboardInterrupt:
            logger.info("用户中断")
        finally:
            video_cap.release()
            if self.args.display:
                cv2.destroyAllWindows()
        
        self._save_results()
        
        duration = time.time() - self.start_time
        logger.info(f"分析完成, 耗时: {duration:.1f}s")
    
    def _save_results(self):
        current_time = time.time() - self.start_time
        self.statistics.update_progress(self.frame_count, current_time)
        
        if self.current_pose:
            self.statistics.finish_pose_tracking(current_time, self.frame_count)
        
        if self.args.output_json:
            output_json = self.args.output_json
            if not output_json:
                output_json = "analysis_results.json"
            self.statistics.save(output_json)
            logger.info(f"统计数据已保存: {output_json}")
        
        if self.args.output_features:
            self.feature_extractor.export_features(self.args.output_features)
            logger.info(f"特征向量已导出: {self.args.output_features}")
        
        if self.args.output_summary:
            summary = self.statistics.get_summary()
            features = self.feature_extractor.extract_features()
            
            summary_image = self.visualizer.create_summary_image(
                summary, 
                features.to_dict() if features else None
            )
            
            cv2.imwrite(self.args.output_summary, summary_image)
            logger.info(f"摘要图像已保存: {self.args.output_summary}")
    
    def get_results(self):
        return {
            "statistics": self.statistics.get_summary(),
            "features": self.feature_extractor.extract_features().to_dict(),
            "engagement_score": self.feature_extractor.calculate_engagement_score(),
            "attention_score": self.feature_extractor.calculate_attention_score()
        }


def parse_args():
    parser = argparse.ArgumentParser(description="智慧课堂教师行为分析系统")
    
    parser.add_argument("--source", type=str, default="0",
                       help="视频源: 摄像头ID 或 视频文件路径 (默认: 0)")
    
    parser.add_argument("--model", type=str, default="yolov8s-pose.pt",
                       help="YOLOv8-Pose模型路径 (默认: yolov8s-pose.pt)")
    
    parser.add_argument("--confidence", type=float, default=0.5,
                       help="置信度阈值 (默认: 0.5)")
    parser.add_argument("--iou", type=float, default=0.45,
                       help="IOU阈值 (默认: 0.45)")
    parser.add_argument("--keypoint_threshold", type=float, default=0.3,
                       help="关键点置信度阈值 (默认: 0.3)")
    
    parser.add_argument("--standing_threshold", type=int, default=5,
                       help="站立检测阈值 (默认: 5)")
    parser.add_argument("--walking_distance", type=int, default=30,
                       help="走动距离阈值 (默认: 30)")
    parser.add_argument("--writing_height", type=int, default=150,
                       help="板书高度阈值 (默认: 150)")
    parser.add_argument("--facing_angle", type=int, default=45,
                       help="面向学生角度阈值 (默认: 45)")
    
    parser.add_argument("--hand_raise_threshold", type=int, default=50,
                       help="举手检测阈值 (默认: 50)")
    parser.add_argument("--head_drop_threshold", type=int, default=30,
                       help="低头检测阈值 (默认: 30)")
    parser.add_argument("--stand_up_threshold", type=int, default=80,
                       help="起立检测阈值 (默认: 80)")
    
    parser.add_argument("--interaction_distance", type=int, default=200,
                       help="互动距离阈值 (默认: 200)")
    parser.add_argument("--time_window", type=int, default=60,
                       help="时间窗口 (默认: 60)")
    
    parser.add_argument("--skip_frames", type=int, default=1,
                       help="跳帧数 (默认: 1)")
    
    parser.add_argument("--output", type=str, default="output.mp4",
                       help="输出视频路径 (默认: output.mp4)")
    parser.add_argument("--output_json", type=str, default="statistics.json",
                       help="输出JSON路径 (默认: statistics.json)")
    parser.add_argument("--output_features", type=str, default="features.json",
                       help="输出特征路径 (默认: features.json)")
    parser.add_argument("--output_summary", type=str, default="summary.jpg",
                       help="输出摘要图像路径 (默认: summary.jpg)")
    
    parser.add_argument("--output_video", action="store_true", default=True,
                       help="保存输出视频")
    parser.add_argument("--visualize", action="store_true", default=True,
                       help="可视化检测结果")
    parser.add_argument("--show_stats", action="store_true", default=True,
                       help="显示统计信息")
    parser.add_argument("--display", action="store_true", default=True,
                       help="显示视频窗口")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    analyzer = ClassroomAnalyzer(args)
    analyzer.initialize()
    
    source = args.source
    
    if source.isdigit():
        camera_id = int(source)
        analyzer.run_camera(camera_id)
    else:
        analyzer.run_video(source)
    
    results = analyzer.get_results()
    
    print("\n" + "="*50)
    print("分析结果:")
    print("="*50)
    print(f"总帧数: {results['statistics']['total_frames']}")
    print(f"总时长: {results['statistics']['total_duration']:.2f}s")
    print(f"互动次数: {results['statistics']['interaction_count']}")
    print(f"互动频率: {results['statistics']['interaction_frequency']:.4f}次/秒")
    print(f"教师走动范围: {results['statistics']['walking_range']:.2f}")
    print(f"课堂投入度: {results['engagement_score']:.4f}")
    print(f"学生注意力: {results['attention_score']:.4f}")
    print("="*50)
    
    return results


if __name__ == "__main__":
    import cv2
    main()