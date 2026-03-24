import os
import random
from dataclasses import dataclass, field
from typing import List
try:
    from typing import Protocol, runtime_checkable
except ImportError:
    from typing_extensions import Protocol, runtime_checkable  # type: ignore


@dataclass
class WordScore:
    word: str
    score: int  # 0-100
    status: str = "good"  # "good" or "weak"


@dataclass
class SpeechAssessmentResult:
    score: int                                    # 0-100 整体评分
    level: str = ""                               # "excellent"/"great"/"good"/"keep_trying"
    word_scores: List[WordScore] = field(default_factory=list)
    feedback: str = ""


@runtime_checkable
class SpeechAssessor(Protocol):
    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        ...


class MockSpeechAssessor:
    """开发/测试用：返回随机评分，不调用任何外部服务"""

    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        score = random.randint(60, 100)
        if score >= 90:
            feedback = "优秀！发音非常标准。"
        elif score >= 70:
            feedback = "良好，继续练习！"
        else:
            feedback = "需要加油，多听多读。"
        return SpeechAssessmentResult(score=score, feedback=feedback)


class AliyunSpeechAssessor:
    """阿里云智能语音交互发音评测实现。

    需要环境变量：
      ALIYUN_ACCESS_KEY_ID
      ALIYUN_ACCESS_KEY_SECRET
      ALIYUN_NLS_APP_KEY

    阿里云 NLS 文档：https://help.aliyun.com/product/30413.html
    具体使用的产品：英语口语评测（nls-speech-assessment）
    音频格式要求：PCM/WAV，16kHz，16bit，单声道
    """

    def __init__(self):
        self._access_key_id = os.environ.get("ALIYUN_ACCESS_KEY_ID", "")
        self._access_key_secret = os.environ.get("ALIYUN_ACCESS_KEY_SECRET", "")
        self._app_key = os.environ.get("ALIYUN_NLS_APP_KEY", "")

    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        """提交 WAV 音频到阿里云发音评测接口，返回评分结果。

        audio_bytes 应为 WAV 格式（16kHz, 16bit, mono）。
        调用方负责在提交前完成格式转换（WebM → WAV）。
        """
        # TODO: 根据实际申请的阿里云产品 SDK 实现调用逻辑
        # 参考：aliyun-python-sdk-core + nls SDK
        # pip install aliyun-python-sdk-core nls-python-sdk
        raise NotImplementedError(
            "AliyunSpeechAssessor 需根据实际申请的阿里云产品配置实现。"
            "请参考 docs/superpowers/specs/2026-03-21-raz-shadowing-design.md 第5节。"
        )


def get_assessor() -> SpeechAssessor:
    """根据环境变量 SPEECH_ASSESSOR 返回对应实现。"""
    provider = os.environ.get("SPEECH_ASSESSOR", "mock").lower()
    if provider == "aliyun":
        return AliyunSpeechAssessor()
    return MockSpeechAssessor()
