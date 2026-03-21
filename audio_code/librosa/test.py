import librosa
import numpy as np

class AudioFeatureExtractor:
    def __init__(self, audio_path, sr=16000):
        self.y, self.sr = librosa.load(audio_path, sr=sr)
        self.duration = len(self.y) / self.sr
        print(f"音频加载完成，时长: {self.duration:.2f} 秒，采样率: {self.sr} Hz")

    def extract_all_features(self, total_words=None):
        """提取所有特征，如果提供了总字数则计算语速"""
        features = {}

        # 1. 时长
        features['duration'] = self.duration

        # 2. 语速
        if total_words:
            features['words_per_minute'] = (total_words / self.duration) * 60

        # 3. 基频统计
        f0, _, _ = librosa.pyin(self.y, fmin=50, fmax=500, sr=self.sr)
        f0_values = f0[~np.isnan(f0)]
        if len(f0_values) > 0:
            features['f0_mean'] = np.mean(f0_values)
            features['f0_median'] = np.median(f0_values)
            features['f0_std'] = np.std(f0_values)
        else:
            features['f0_mean'] = features['f0_median'] = features['f0_std'] = 0

        # 4. 短时能量统计
        energy = librosa.feature.rms(y=self.y)[0]
        features['energy_mean'] = np.mean(energy)
        features['energy_std'] = np.std(energy)
        features['energy_max'] = np.max(energy)

        # 5. MFCC特征 (返回13维系数的均值)
        mfccs = librosa.feature.mfcc(y=self.y, sr=self.sr, n_mfcc=13)
        # 对每个系数取时间轴上的均值
        mfccs_mean = np.mean(mfccs, axis=1)
        for i, val in enumerate(mfccs_mean):
            features[f'mfcc_{i+1}'] = val

        return features

# 使用示例
extractor = AudioFeatureExtractor('/home/next_lb/桌面/next/面向智慧课堂的教师语音特征可视化与风格画像系统/audio_code/ten-vad/examples/s0724-s0730.wav')
all_features = extractor.extract_all_features(total_words=50)  # 假设有50个字
print(all_features)





