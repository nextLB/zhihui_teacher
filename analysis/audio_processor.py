"""
语音处理模块
实现音频分析的相关功能
"""

import os
import sys
import json
import re
import subprocess
import tempfile
import shutil
from typing import Dict, Any, Optional, List, Tuple
from django.conf import settings

try:
    import numpy as np
except ImportError:
    np = None

audio_code_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'audio_code')
sys.path.insert(0, audio_code_path)


class AudioPreprocessor:
    """音频预处理器"""

    @staticmethod
    def load_audio(file_path: str, sample_rate: int = 16000):
        """加载音频文件"""
        try:
            import librosa
            audio, sr = librosa.load(file_path, sr=sample_rate)
            return audio, sr
        except Exception as e:
            print(f"音频加载失败: {e}")
            return np.array([]), sample_rate

    @staticmethod
    def voice_activity_detection(audio_data, sample_rate: int = 16000) -> List[Tuple[int, int]]:
        """语音活动检测 (VAD)"""
        try:
            import librosa
            hop_size = 256
            num_frames = len(audio_data) // hop_size
            
            vad_segments = []
            current_start = None
            
            energy_threshold = 0.02
            frame_length = hop_size
            
            for i in range(num_frames):
                frame = audio_data[i * hop_size:(i + 1) * hop_size]
                energy = np.sqrt(np.mean(frame ** 2))
                
                is_speech = energy > energy_threshold
                
                if is_speech and current_start is None:
                    current_start = i
                elif not is_speech and current_start is not None:
                    vad_segments.append((current_start, i))
                    current_start = None
            
            if current_start is not None:
                vad_segments.append((current_start, num_frames))
            
            return vad_segments
        except Exception as e:
            print(f"VAD检测失败: {e}")
            return [(0, len(audio_data) // 256)]

    @staticmethod
    def extract_audio_duration(file_path: str) -> float:
        """获取音频文件时长"""
        try:
            import librosa
            duration = librosa.get_duration(path=file_path)
            return duration
        except:
            return 0.0

    @staticmethod
    def convert_to_wav(input_path: str) -> str:
        """转换音频为WAV格式"""
        output_path = input_path.replace(os.path.splitext(input_path)[1], '_converted.wav')
        
        if os.path.exists(output_path):
            return output_path
        
        try:
            result = subprocess.run([
                'ffmpeg', '-i', input_path, '-ar', '16000', '-ac', '1',
                '-y', output_path
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                return output_path
        except:
            pass
        
        return input_path


class AudioFeatureExtractor:
    """语音特征提取器"""

    @staticmethod
    def extract_speech_rate(text: str, duration: float) -> float:
        """提取语速特征"""
        if not text or duration <= 0:
            return 0.0
        
        word_count = len(text)
        speech_rate = (word_count / duration) * 60
        return min(speech_rate, 300)

    @staticmethod
    def extract_pitch_frequency(audio_data, sample_rate: int = 16000) -> float:
        """提取音高基频特征"""
        try:
            import librosa
            f0, _, _ = librosa.pyin(audio_data, fmin=50, fmax=500, sr=sample_rate)
            f0_values = f0[~np.isnan(f0)]
            if len(f0_values) > 0:
                return float(np.mean(f0_values))
            return 0.0
        except Exception as e:
            print(f"音高提取失败: {e}")
            return 0.0

    @staticmethod
    def extract_short_time_energy(audio_data, sample_rate: int = 16000) -> float:
        """提取短时能量特征"""
        try:
            import librosa
            energy = librosa.feature.rms(y=audio_data)[0]
            return float(np.mean(energy))
        except:
            return 0.0

    @staticmethod
    def extract_mfcc(audio_data, sample_rate: int = 16000, n_mfcc: int = 13) -> Dict[str, float]:
        """提取MFCC特征"""
        try:
            import librosa
            mfccs = librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=n_mfcc)
            mfccs_mean = np.mean(mfccs, axis=1)
            return {f'mfcc_{i+1}': float(mfccs_mean[i]) for i in range(n_mfcc)}
        except Exception as e:
            print(f"MFCC提取失败: {e}")
            return {f'mfcc_{i+1}': 0.0 for i in range(n_mfcc)}


class ToneClassifier:
    """语气分类器"""
    
    TONE_TYPES = ['鼓励型', '引导型', '讲授型', '中性型']

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None

    def predict(self, features: Dict[str, Any]) -> Tuple[str, float]:
        """预测语气类型"""
        speech_rate = features.get('speech_rate', 0)
        pitch = features.get('pitch_frequency', 0)
        energy = features.get('short_time_energy', 0)
        
        if speech_rate > 180 and energy > 0.05:
            tone_type = '鼓励型'
            confidence = 0.75
        elif 120 <= speech_rate <= 180 and pitch > 200:
            tone_type = '引导型'
            confidence = 0.70
        elif speech_rate < 120 and pitch < 180:
            tone_type = '讲授型'
            confidence = 0.72
        else:
            tone_type = '中性型'
            confidence = 0.60
        
        return tone_type, confidence


class SpeechRecognizer:
    """语音识别器"""

    def __init__(self, model_size: str = 'tiny'):
        self.model_size = model_size
        self.model = None

    def load_model(self):
        """加载模型"""
        if self.model is not None:
            return
        
        try:
            import whisper
            whisper_path = os.path.join(audio_code_path, 'whisper')
            model_path = os.path.join(whisper_path, 'models')
            
            try:
                self.model = whisper.load_model(self.model_size, device='cpu')
            except:
                self.model = whisper.load_model(self.model_size)
            print("Whisper模型加载成功")
        except Exception as e:
            print(f"Whisper模型加载失败: {e}")

    def recognize(self, audio_data: any, sample_rate: int = 16000) -> str:
        """语音识别"""
        try:
            self.load_model()
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                try:
                    import scipy.io.wavfile as wav
                    wav.write(tmp.name, sample_rate, (audio_data * 32767).astype(np.int16))
                    result = self.model.transcribe(tmp.name, language='zh', fp16=False)
                    return result.get('text', '')
                finally:
                    os.unlink(tmp.name)
        except Exception as e:
            print(f"语音识别失败: {e}")
            return ''

    def recognize_from_file(self, file_path: str) -> str:
        """从文件进行语音识别"""
        try:
            self.load_model()
            
            wav_path = AudioPreprocessor.convert_to_wav(file_path)
            result = self.model.transcribe(wav_path, language='zh', fp16=False)
            return result.get('text', '')
        except Exception as e:
            print(f"语音识别失败: {e}")
            return ''


class SemanticAnalyzer:
    """语义分析器"""

    @staticmethod
    def analyze_question_types(text: str) -> Dict[str, int]:
        """分析提问类型"""
        if not text:
            return {'是何': 0, '为何': 0, '如何': 0, '其他': 0}
        
        patterns = {
            '是何': r'什么|哪|谁|有没有|是不是|是不是|多少|幾',
            '为何': r'为什么|為什麼|为何|为何|什么原因|怎麼會',
            '如何': r'如何|怎麼|怎样|怎樣|怎样才能|如何才能'
        }
        
        result = {}
        for qtype, pattern in patterns.items():
            result[qtype] = len(re.findall(pattern, text))
        
        total_questions = sum(result.values())
        question_marks = len(re.findall(r'[？?]', text))
        result['其他'] = max(0, question_marks - total_questions)
        
        return result

    @staticmethod
    def calculate_utterance_length(text: str) -> float:
        """计算平均话语长度"""
        if not text:
            return 0.0
        
        sentences = re.split(r'[。！？；\n]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        total_chars = sum(len(s) for s in sentences)
        return total_chars / len(sentences)


def analyze_audio(file_path: str, audio_id: int = None) -> Dict[str, Any]:
    """完整的音频分析流程"""
    
    def update_progress(stage: str, progress: float, message: str = ''):
        if audio_id:
            progress_file = os.path.join(settings.MEDIA_ROOT, f'audio_{audio_id}_progress.json')
            progress_data = {
                'stage': stage,
                'progress': progress,
                'message': message
            }
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f)
        print(f"[音频分析] {stage}: {progress*100:.0f}% {message}")
    
    try:
        import librosa
    except ImportError:
        return {
            'speech_rate': 0, 'pitch_frequency': 0, 'short_time_energy': 0,
            'mfcc': {}, 'tone_type': '中性型', 'tone_confidence': 0,
            'transcribed_text': '', 'question_types': {},
            'utterance_length_avg': 0, 'valid_speech_duration': 0, 'silence_duration': 0
        }
    
    try:
        update_progress('加载音频', 0.1, '正在加载音频文件...')
        wav_path = AudioPreprocessor.convert_to_wav(file_path)
        audio_data, sample_rate = AudioPreprocessor.load_audio(wav_path)
        
        if len(audio_data) == 0:
            return {
                'speech_rate': 0, 'pitch_frequency': 0, 'short_time_energy': 0,
                'mfcc': {}, 'tone_type': '中性型', 'tone_confidence': 0,
                'transcribed_text': '', 'question_types': {},
                'utterance_length_avg': 0, 'valid_speech_duration': 0, 'silence_duration': 0
            }
        
        duration = len(audio_data) / sample_rate
        update_progress('VAD检测', 0.2, '正在检测语音活动...')
        
        speech_segments = AudioPreprocessor.voice_activity_detection(audio_data, sample_rate)
        
        update_progress('提取声学特征', 0.4, '正在提取音高和能量特征...')
        
        valid_duration = sum((end - start) * 256 / sample_rate for start, end in speech_segments)
        silence_duration = duration - valid_duration
        
        pitch_frequency = AudioFeatureExtractor.extract_pitch_frequency(audio_data, sample_rate)
        short_time_energy = AudioFeatureExtractor.extract_short_time_energy(audio_data, sample_rate)
        
        update_progress('提取MFCC特征', 0.5, '正在计算MFCC...')
        mfcc_features = AudioFeatureExtractor.extract_mfcc(audio_data, sample_rate)
        
        update_progress('语音识别', 0.6, '正在识别语音内容(Whisper)...')
        
        classifier = ToneClassifier()
        
        try:
            recognizer = SpeechRecognizer(model_size='tiny')
            transcribed_text = recognizer.recognize_from_file(wav_path)
            update_progress('语音识别完成', 0.8, f'识别到 {len(transcribed_text)} 个字符')
        except Exception as e:
            print(f"语音识别失败: {e}")
            transcribed_text = ''
        
        speech_rate = AudioFeatureExtractor.extract_speech_rate(transcribed_text, duration)
        
        update_progress('语义分析', 0.9, '正在分析提问类型...')
        
        features = {
            'speech_rate': speech_rate,
            'pitch_frequency': pitch_frequency,
            'short_time_energy': short_time_energy,
            'mfcc': mfcc_features
        }
        tone_type, tone_confidence = classifier.predict(features)
        
        question_types = SemanticAnalyzer.analyze_question_types(transcribed_text)
        utterance_length_avg = SemanticAnalyzer.calculate_utterance_length(transcribed_text)
        
        update_progress('完成', 1.0, '分析完成!')
        
        if audio_id:
            progress_file = os.path.join(settings.MEDIA_ROOT, f'audio_{audio_id}_progress.json')
            progress_data = {
                'stage': 'completed',
                'progress': 1.0,
                'duration': duration,
                'text_length': len(transcribed_text)
            }
            with open(progress_file, 'w') as f:
                json.dump(progress_data, f)
        
        return {
            'speech_rate': speech_rate,
            'pitch_frequency': pitch_frequency,
            'short_time_energy': short_time_energy,
            'mfcc': mfcc_features,
            'tone_type': tone_type,
            'tone_confidence': tone_confidence,
            'transcribed_text': transcribed_text,
            'question_types': question_types,
            'utterance_length_avg': utterance_length_avg,
            'valid_speech_duration': int(valid_duration),
            'silence_duration': int(silence_duration)
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'speech_rate': 0, 'pitch_frequency': 0, 'short_time_energy': 0,
            'mfcc': {}, 'tone_type': '中性型', 'tone_confidence': 0,
            'transcribed_text': '', 'question_types': {},
            'utterance_length_avg': 0, 'valid_speech_duration': 0, 'silence_duration': 0
        }