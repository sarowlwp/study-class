import os
import random
import asyncio
from io import BytesIO
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


def _extract_audio_duration(audio_bytes: bytes) -> float:
    """Extract audio duration in seconds from audio bytes."""
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(BytesIO(audio_bytes))
        return len(audio) / 1000.0  # Convert ms to seconds
    except Exception:
        # If we can't determine duration, return a safe value
        return 5.0


class AzureSpeechAssessor:
    """Microsoft Azure Speech Service 发音评估实现。

    环境变量:
      AZURE_SPEECH_KEY - 语音服务密钥
      AZURE_SPEECH_REGION - 服务区域 (如 eastasia, westus2)

    参考文档: https://learn.microsoft.com/azure/ai-services/speech-service/how-to-pronunciation-assessment
    """

    def __init__(self):
        self._key = os.environ.get("AZURE_SPEECH_KEY")
        self._region = os.environ.get("AZURE_SPEECH_REGION")
        if not self._key:
            raise ValueError("Azure Speech 评估器需要环境变量 AZURE_SPEECH_KEY")
        if not self._region:
            raise ValueError("Azure Speech 评估器需要环境变量 AZURE_SPEECH_REGION")
        self._max_retries = 3
        self._audio_duration_min = 1.0   # seconds
        self._audio_duration_max = 60.0  # seconds

    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        """评估音频发音。

        Args:
            audio_bytes: 音频数据 (WebM/Opus 格式)
            text: 参考文本

        Returns:
            SpeechAssessmentResult 包含评分和单词级反馈
        """
        # Validate audio duration
        duration = _extract_audio_duration(audio_bytes)
        if duration < self._audio_duration_min:
            raise ValueError(f"录音过短 ({duration:.1f}s)，请重新录制")
        if duration > self._audio_duration_max:
            raise ValueError(f"录音过长 ({duration:.1f}s)，请分段录制")

        # Try direct submission first
        try:
            return await self._assess_with_azure(audio_bytes, text)
        except ValueError as e:
            if "format" in str(e).lower() or "codec" in str(e).lower():
                # Try converting to WAV
                try:
                    wav_bytes = self._convert_to_wav(audio_bytes)
                    return await self._assess_with_azure(wav_bytes, text)
                except Exception as convert_error:
                    raise ValueError(f"音频格式不支持: {convert_error}")
            raise

    def _convert_to_wav(self, audio_bytes: bytes) -> bytes:
        """Convert audio to 16kHz WAV format."""
        from pydub import AudioSegment
        audio = AudioSegment.from_file(BytesIO(audio_bytes))
        # Convert to 16kHz, 16bit, mono
        audio = audio.set_frame_rate(16000).set_sample_width(2).set_channels(1)
        output = BytesIO()
        audio.export(output, format="wav")
        return output.getvalue()

    async def _assess_with_azure(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        """Call Azure Speech Service with retry logic."""
        import azure.cognitiveservices.speech as speechsdk

        last_error = None
        for attempt in range(self._max_retries):
            try:
                return await self._call_azure_api(audio_bytes, text)
            except (speechsdk.CancellationError, ConnectionError, TimeoutError) as e:
                last_error = e
                if attempt < self._max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1, 2, 4 seconds
                    await asyncio.sleep(wait_time)
                continue
            except Exception as e:
                # Don't retry on other errors (4xx, etc.)
                raise RuntimeError(f"Azure Speech API error: {e}")

        raise RuntimeError(f"Azure Speech 服务暂时不可用，请稍后重试: {last_error}")

    async def _call_azure_api(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        """Make single call to Azure Speech API."""
        import azure.cognitiveservices.speech as speechsdk

        # Create speech config
        speech_config = speechsdk.SpeechConfig(subscription=self._key, region=self._region)

        # Create pronunciation assessment config
        pronunciation_config = speechsdk.PronunciationAssessmentConfig(
            reference_text=text,
            grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
            granularity=speechsdk.PronunciationAssessmentGranularity.Word,
            enable_miscue=True
        )

        # Create audio input from bytes
        push_stream = speechsdk.audio.PushAudioInputStream()
        audio_input = speechsdk.AudioConfig(stream=push_stream)
        push_stream.write(audio_bytes)
        push_stream.close()

        # Create speech recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_input,
            language="en-US"
        )
        pronunciation_config.apply_to(speech_recognizer)

        # Recognize speech
        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            raise speechsdk.CancellationError(f"Speech recognition canceled: {cancellation_details.reason}")

        if result.reason != speechsdk.ResultReason.RecognizedSpeech:
            raise RuntimeError(f"Speech recognition failed: {result.reason}")

        # Parse pronunciation assessment result
        pronunciation_result = speechsdk.PronunciationAssessmentResult(result)

        # Map scores to our format
        overall_score = round(pronunciation_result.pronunciation_score)
        level, feedback = self._map_score_to_level(overall_score)

        # Map word scores
        word_scores = []
        for word in pronunciation_result.words:
            word_score = round(word.accuracy_score)
            word_scores.append(WordScore(
                word=word.word,
                score=word_score,
                status=self._map_word_score(word_score)
            ))

        return SpeechAssessmentResult(
            score=overall_score,
            level=level,
            feedback=feedback,
            word_scores=word_scores
        )

    def _map_score_to_level(self, score: int) -> tuple[str, str]:
        """Map score to four-tier level and feedback."""
        if score >= 90:
            return ("excellent", "非常棒 🌟🌟")
        elif score >= 75:
            return ("great", "很好 🌟")
        elif score >= 60:
            return ("good", "不错 👍")
        else:
            return ("keep_trying", "继续加油 💪")

    def _map_word_score(self, score: int) -> str:
        """Map word score to status."""
        return "good" if score >= 70 else "weak"


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
