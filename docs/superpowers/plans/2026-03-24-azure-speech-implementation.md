# Azure Speech Pronunciation Assessment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 集成 Microsoft Azure Speech Service 到 RAZ 跟读模块，提供准确的发音评估能力

**Architecture:** 新增 `AzureSpeechAssessor` 类实现 `SpeechAssessor` 协议，通过 `get_assessor()` 工厂函数根据 `SPEECH_ASSESSOR` 环境变量切换实现。Azure 评估器将音频提交到 Azure Speech Service，返回四级制评分和单词级反馈。

**Tech Stack:** Python 3.10+, FastAPI, Azure Cognitive Services Speech SDK, pydub (音频转换)

**Design Spec:** `docs/superpowers/specs/2026-03-24-raz-azure-speech-design.md`

---

## File Structure

| 文件 | 职责 | 变更类型 |
|-----|------|---------|
| `requirements.txt` | 添加 Azure Speech SDK 依赖 | 修改 |
| `app/services/speech_assessment.py` | 添加 `AzureSpeechAssessor` 类，更新数据类和工厂函数 | 修改 |
| `tests/test_speech_assessment.py` | 添加 Azure 评估器的单元测试 | 修改 |
| `.env.example` | 添加 Azure Speech 环境变量示例 | 新增 |

---

## Task 1: Add Azure Speech SDK Dependency

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: Add dependency**

```bash
# Add to requirements.txt
echo "azure-cognitiveservices-speech>=1.35.0" >> requirements.txt
```

- [ ] **Step 2: Verify dependency added**

```bash
tail -5 requirements.txt
```

Expected output: 包含 `azure-cognitiveservices-speech>=1.35.0`

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "deps: add azure-cognitiveservices-speech SDK

Add Microsoft Azure Speech Service SDK for pronunciation assessment.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 2: Update Data Classes

**Files:**
- Modify: `app/services/speech_assessment.py:11-21`

- [ ] **Step 1: Write test for updated WordScore**

```python
# tests/test_speech_assessment.py - add after existing imports
from app.services.speech_assessment import WordScore, SpeechAssessmentResult


def test_word_score_has_status_field():
    ws = WordScore(word="hello", score=85)
    assert ws.word == "hello"
    assert ws.score == 85
    assert ws.status == "good"  # default value


def test_word_score_status_can_be_weak():
    ws = WordScore(word="hello", score=55, status="weak")
    assert ws.status == "weak"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /Users/liuwenping/Documents/fliggy/study-class
python -m pytest tests/test_speech_assessment.py::test_word_score_has_status_field -v
```

Expected: FAIL - `TypeError: WordScore.__init__() got an unexpected keyword argument 'status'`

- [ ] **Step 3: Add status field to WordScore**

```python
# app/services/speech_assessment.py - modify WordScore class
@dataclass
class WordScore:
    word: str
    score: int  # 0-100
    status: str = "good"  # "good" or "weak"
```

- [ ] **Step 4: Add level field to SpeechAssessmentResult**

```python
# app/services/speech_assessment.py - modify SpeechAssessmentResult class
@dataclass
class SpeechAssessmentResult:
    score: int                                    # 0-100 整体评分
    level: str = ""                               # "excellent"/"great"/"good"/"keep_trying"
    word_scores: List[WordScore] = field(default_factory=list)
    feedback: str = ""
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
python -m pytest tests/test_speech_assessment.py::test_word_score_has_status_field tests/test_speech_assessment.py::test_word_score_status_can_be_weak -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add app/services/speech_assessment.py tests/test_speech_assessment.py
git commit -m "feat(speech): add level and status fields to assessment result

- Add status field to WordScore (default: good)
- Add level field to SpeechAssessmentResult for four-tier scoring

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 3: Implement AzureSpeechAssessor

**Files:**
- Modify: `app/services/speech_assessment.py` (add new class after AliyunSpeechAssessor)

- [ ] **Step 1: Write test for AzureSpeechAssessor initialization**

```python
# tests/test_speech_assessment.py
import os
import pytest
from unittest.mock import patch


class TestAzureSpeechAssessor:
    def test_init_raises_without_key(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "", "AZURE_SPEECH_REGION": ""}):
            with pytest.raises(ValueError, match="AZURE_SPEECH_KEY"):
                from app.services.speech_assessment import AzureSpeechAssessor
                AzureSpeechAssessor()

    def test_init_raises_without_region(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test-key", "AZURE_SPEECH_REGION": ""}):
            with pytest.raises(ValueError, match="AZURE_SPEECH_REGION"):
                from app.services.speech_assessment import AzureSpeechAssessor
                AzureSpeechAssessor()

    def test_init_succeeds_with_both_env_vars(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test-key", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._key == "test-key"
            assert assessor._region == "eastasia"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_speech_assessment.py::TestAzureSpeechAssessor -v
```

Expected: FAIL - `ImportError: cannot import name 'AzureSpeechAssessor'`

- [ ] **Step 3: Implement AzureSpeechAssessor class**

```python
# app/services/speech_assessment.py - add after AliyunSpeechAssessor class

import asyncio
from io import BytesIO


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
```

- [ ] **Step 4: Run tests to verify initialization**

```bash
python -m pytest tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_init_raises_without_key tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_init_raises_without_region tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_init_succeeds_with_both_env_vars -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/speech_assessment.py tests/test_speech_assessment.py
git commit -m "feat(speech): implement AzureSpeechAssessor class

- Add Azure Speech Service integration with pronunciation assessment
- Implement audio format conversion (WebM -> WAV fallback)
- Add retry logic with exponential backoff
- Map Azure scores to four-tier level system

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 4: Update get_assessor() Factory Function

**Files:**
- Modify: `app/services/speech_assessment.py:77-82` (update get_assessor function)

- [ ] **Step 1: Write test for get_assessor with azure**

```python
# tests/test_speech_assessment.py - add to existing tests

class TestGetAssessor:
    def test_returns_mock_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            from app.services.speech_assessment import get_assessor, MockSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, MockSpeechAssessor)

    def test_returns_mock_when_mock_specified(self):
        with patch.dict(os.environ, {"SPEECH_ASSESSOR": "mock"}):
            from app.services.speech_assessment import get_assessor, MockSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, MockSpeechAssessor)

    def test_returns_azure_when_azure_specified(self):
        with patch.dict(os.environ, {
            "SPEECH_ASSESSOR": "azure",
            "AZURE_SPEECH_KEY": "test-key",
            "AZURE_SPEECH_REGION": "eastasia"
        }):
            from app.services.speech_assessment import get_assessor, AzureSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, AzureSpeechAssessor)

    def test_returns_mock_for_invalid_provider(self):
        with patch.dict(os.environ, {"SPEECH_ASSESSOR": "invalid"}):
            from app.services.speech_assessment import get_assessor, MockSpeechAssessor
            assessor = get_assessor()
            assert isinstance(assessor, MockSpeechAssessor)
```

- [ ] **Step 2: Run test to verify azure case fails**

```bash
python -m pytest tests/test_speech_assessment.py::TestGetAssessor::test_returns_azure_when_azure_specified -v
```

Expected: FAIL - returns MockSpeechAssessor instead of AzureSpeechAssessor

- [ ] **Step 3: Update get_assessor() function**

```python
# app/services/speech_assessment.py - replace existing get_assessor function

def get_assessor() -> SpeechAssessor:
    """根据环境变量 SPEECH_ASSESSOR 返回对应实现。"""
    provider = os.environ.get("SPEECH_ASSESSOR", "mock").lower()
    if provider == "aliyun":
        return AliyunSpeechAssessor()
    if provider == "azure":
        return AzureSpeechAssessor()
    return MockSpeechAssessor()
```

- [ ] **Step 4: Run all get_assessor tests**

```bash
python -m pytest tests/test_speech_assessment.py::TestGetAssessor -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/services/speech_assessment.py tests/test_speech_assessment.py
git commit -m "feat(speech): add azure option to get_assessor factory

- Update get_assessor() to return AzureSpeechAssessor when SPEECH_ASSESSOR=azure
- Add tests for factory function with all providers

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 5: Add Score Mapping Tests

**Files:**
- Modify: `tests/test_speech_assessment.py`

- [ ] **Step 1: Write tests for score mapping**

```python
# tests/test_speech_assessment.py - add to TestAzureSpeechAssessor class

    def test_map_score_to_level_excellent(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(90) == ("excellent", "非常棒 🌟🌟")
            assert assessor._map_score_to_level(100) == ("excellent", "非常棒 🌟🌟")

    def test_map_score_to_level_great(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(75) == ("great", "很好 🌟")
            assert assessor._map_score_to_level(89) == ("great", "很好 🌟")

    def test_map_score_to_level_good(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(60) == ("good", "不错 👍")
            assert assessor._map_score_to_level(74) == ("good", "不错 👍")

    def test_map_score_to_level_keep_trying(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_score_to_level(0) == ("keep_trying", "继续加油 💪")
            assert assessor._map_score_to_level(59) == ("keep_trying", "继续加油 💪")

    def test_map_word_score_good(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_word_score(70) == "good"
            assert assessor._map_word_score(100) == "good"

    def test_map_word_score_weak(self):
        with patch.dict(os.environ, {"AZURE_SPEECH_KEY": "test", "AZURE_SPEECH_REGION": "eastasia"}):
            from app.services.speech_assessment import AzureSpeechAssessor
            assessor = AzureSpeechAssessor()
            assert assessor._map_word_score(0) == "weak"
            assert assessor._map_word_score(69) == "weak"
```

- [ ] **Step 2: Run score mapping tests**

```bash
python -m pytest tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_map_score_to_level_excellent tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_map_score_to_level_great tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_map_score_to_level_good tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_map_score_to_level_keep_trying tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_map_word_score_good tests/test_speech_assessment.py::TestAzureSpeechAssessor::test_map_word_score_weak -v
```

Expected: PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_speech_assessment.py
git commit -m "test(speech): add score mapping tests for Azure assessor

- Add tests for four-tier level mapping
- Add tests for word status mapping (good/weak threshold)

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 6: Create .env.example File

**Files:**
- Create: `.env.example`

- [ ] **Step 1: Create .env.example**

```bash
cat > .env.example << 'EOF'
# Azure Speech Service Configuration
SPEECH_ASSESSOR=azure
AZURE_SPEECH_KEY=your-azure-speech-key-here
AZURE_SPEECH_REGION=eastasia

# Alternative: Aliyun Speech (if using Aliyun instead of Azure)
# SPEECH_ASSESSOR=aliyun
# ALIYUN_ACCESS_KEY_ID=your-access-key
# ALIYUN_ACCESS_KEY_SECRET=your-secret
# ALIYUN_NLS_APP_KEY=your-app-key

# Default: Mock Speech Assessor (for development)
# SPEECH_ASSESSOR=mock
EOF
```

- [ ] **Step 2: Verify file created**

```bash
cat .env.example
```

Expected: 显示上述内容

- [ ] **Step 3: Commit**

```bash
git add .env.example
git commit -m "docs: add .env.example with Azure Speech configuration

Add example environment variables for Azure Speech Service setup.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Task 7: Run All Tests

**Files:**
- Run: All test files

- [ ] **Step 1: Run full test suite**

```bash
cd /Users/liuwenping/Documents/fliggy/study-class
python -m pytest tests/test_speech_assessment.py -v
```

Expected: All tests pass

- [ ] **Step 2: Verify no regressions**

```bash
python -m pytest tests/ -v --tb=short
```

Expected: All existing tests still pass

- [ ] **Step 3: Commit if any fixes needed**

```bash
# Only if fixes were made
git add -A
git commit -m "fix: address test regressions

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Verification Checklist

After completing all tasks, verify:

- [ ] `azure-cognitiveservices-speech>=1.35.0` in requirements.txt
- [ ] `WordScore` has `status` field with default "good"
- [ ] `SpeechAssessmentResult` has `level` field
- [ ] `AzureSpeechAssessor` class exists with all methods
- [ ] `get_assessor()` returns `AzureSpeechAssessor` when `SPEECH_ASSESSOR=azure`
- [ ] All new tests pass
- [ ] All existing tests still pass
- [ ] `.env.example` file created with Azure config

---

## Post-Implementation Notes

**Manual Testing Required:**
1. Set environment variables with real Azure credentials
2. Run application and test `/api/raz/assess` endpoint
3. Verify audio format compatibility (WebM direct vs WAV conversion)
4. Verify four-tier scoring displays correctly in UI

**Known Limitations:**
- `_call_azure_api` uses `recognize_once()` which may need adjustment for very long audio
- Audio duration detection uses pydub which requires ffmpeg installed on system
- Azure SDK streaming implementation may need refinement based on actual testing

**Future Improvements:**
- Consider caching assessment results for identical text/audio
- Add metrics/logging for Azure API usage and latency
- Consider adding phoneme-level feedback when needed
