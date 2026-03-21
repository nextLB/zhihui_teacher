#!/usr/bin/env python3
"""
简单测试脚本 - 验证各个模块是否正常工作
"""

import sys
sys.path.insert(0, 'code')

def test_imports():
    print("测试模块导入...")
    
    try:
        from src.video_capture import VideoCapture, VideoWriter
        print("  video_capture: OK")
    except Exception as e:
        print(f"  video_capture: FAIL - {e}")
    
    try:
        from src.detector import PoseDetector, Detection
        print("  detector: OK")
    except Exception as e:
        print(f"  detector: FAIL - {e}")
    
    try:
        from src.pose_estimator import PoseEstimator, TeacherPose, StudentBehavior
        print("  pose_estimator: OK")
    except Exception as e:
        print(f"  pose_estimator: FAIL - {e}")
    
    try:
        from src.behavior_recognizer import BehaviorRecognizer
        print("  behavior_recognizer: OK")
    except Exception as e:
        print(f"  behavior_recognizer: FAIL - {e}")
    
    try:
        from src.statistics import ClassroomStatistics
        print("  statistics: OK")
    except Exception as e:
        print(f"  statistics: FAIL - {e}")
    
    try:
        from src.feature_extractor import FeatureExtractor
        print("  feature_extractor: OK")
    except Exception as e:
        print(f"  feature_extractor: FAIL - {e}")
    
    try:
        from src.visualizer import Visualizer
        print("  visualizer: OK")
    except Exception as e:
        print(f"  visualizer: FAIL - {e}")
    
    print("导入测试完成")

def test_basic_functionality():
    print("\n测试基本功能...")
    
    from src.statistics import ClassroomStatistics
    from src.feature_extractor import FeatureExtractor
    
    stats = ClassroomStatistics()
    stats.start_pose_tracking("站立", 0.0, 0)
    stats.finish_pose_tracking(10.0, 100)
    
    stats.add_student_behavior("举手", 5.0, 50)
    stats.add_student_behavior("举手", 7.0, 70)
    
    stats.update_progress(100, 10.0)
    
    print(f"  教师姿态时间比: {stats.get_teacher_pose_time_ratio()}")
    print(f"  学生行为统计: {stats.get_student_behavior_counts()}")
    print(f"  互动次数: {stats.get_interaction_count()}")
    
    extractor = FeatureExtractor()
    extractor.set_statistics(stats)
    features = extractor.extract_features()
    
    print(f"  特征向量: {features.to_dict()}")
    print(f"  课堂投入度: {extractor.calculate_engagement_score():.4f}")
    print(f"  学生注意力: {extractor.calculate_attention_score():.4f}")
    
    print("基本功能测试完成")

if __name__ == "__main__":
    print("="*50)
    print("智慧课堂教师行为分析系统 - 测试")
    print("="*50)
    
    test_imports()
    test_basic_functionality()
    
    print("\n" + "="*50)
    print("测试完成!")
    print("="*50)