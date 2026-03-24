# RAZ Azure Speech 发音评估集成设计

**日期**: 2026-03-24
**范围**: 新增 Microsoft Azure Speech 服务作为 RAZ 跟读的发音评估引擎

---

## 1. 目标

为 RAZ 跟读模块增加 Microsoft Azure Speech Service 发音评估能力，提供比 Mock 评估器更准确的儿童英语口语评测。

## 2. 核心需求

- **面向用户**: 儿童（简洁友好的反馈）
- **评估维度**: 基础评分 + 单词级评分
- **反馈方式**: 四级制评分 + 整句展示 + 标记待改进单词（< 70 分）
- **部署方式**: 通过环境变量配置，与现有 Mock/Aliyun 评估器共存

## 3. 架构设计

### 3.1 组件关系

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端 (practice.html)                       │
│                    WebM录音 → 上传 /api/raz/assess              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      raz.py (API 路由)                           │
│              assessor = get_assessor() # 根据环境变量返回         │
│                      result = await assessor.assess(...)        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              speech_assessment.py (评估器实现)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ MockSpeech   │  │AliyunSpeech  │  │  AzureSpeechAssessor │  │
│  │  Assessor    │  │  Assessor    │  │    (新增)            │  │
│  │  (开发/测试)  │  │  (未完成)    │  │  SPEECH_ASSESSOR=azure│  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 评估器选择逻辑

```python
def get_assessor() -> SpeechAssessor:
    provider = os.environ.get("SPEECH_ASSESSOR", "mock").lower()
    if provider == "aliyun":
        return AliyunSpeechAssessor()
    if provider == "azure":
        return AzureSpeechAssessor()
    return MockSpeechAssessor()
```

## 4. Azure Speech 集成详情

### 4.1 环境变量

| 变量名 | 说明 | 示例 |
|-------|------|------|
| `SPEECH_ASSESSOR` | 评估器类型 | `azure` |
| `AZURE_SPEECH_KEY` | Azure Speech 服务密钥 | `a1b2c3d4e5f6...` |
| `AZURE_SPEECH_REGION` | 服务区域 | `eastasia`, `westus2` |

### 4.2 评估配置

```python
{
    "reference_text": "用户跟读的目标句子",
    "grading_system": "hundred_mark",  # 百分制
    "granularity": "word",             # 单词级粒度
    "dimension": "comprehensive"       # 综合评分
}
```

### 4.3 音频格式策略（渐进式）

**处理流程**:

```
前端 WebM 音频
      │
      ▼
┌─────────────────┐
│ 尝试直接提交    │
│ Azure Speech    │
└─────────────────┘
      │
      ├─ 成功 → 返回评分结果
      │
      └─ 失败 (格式不支持)
            │
            ▼
      ┌─────────────────┐
      │ 后端转换为 WAV  │
      │ (16kHz, 16bit)  │
      └─────────────────┘
            │
            ├─ 成功 → 重新提交 Azure
            │
            └─ 失败 → 返回 400 错误
```

**格式要求**:
- Azure Speech SDK 支持多种格式（WAV、MP3、OGG、Opus 等）
- 优先尝试直接传递 WebM（浏览器 MediaRecorder 原生格式）
- 转换时使用 `pydub` 库转换为 16kHz WAV

### 4.4 评分映射

**分数处理规则**:
- Azure 可能返回小数，统一使用 `round()` 四舍五入为整数
- 边界值处理：≥ 下限，< 上限（例如 75-89 包含 75，不包含 90）

**整句四级制**

| 分数范围 | 等级(level) | 反馈文字(feedback) |
|---------|------------|-------------------|
| 90-100 | excellent | 非常棒 🌟🌟 |
| 75-89 | great | 很好 🌟 |
| 60-74 | good | 不错 👍 |
| 0-59 | keep_trying | 继续加油 💪 |

**单词状态**

| 单词分数 | 状态(status) | 说明 |
|---------|-------------|------|
| ≥ 70 | good | 发音良好 |
| < 70 | weak | 待改进 |

## 5. API 响应格式

### 5.1 与现有格式兼容

保持与现有代码的兼容性，只增加必要的字段：

**现有格式** (`raz.py` 第 148-152 行):
```json
{
  "score": 85,
  "feedback": "很好 🌟",
  "word_scores": [{"word": "Hello", "score": 95}, ...]
}
```

**新格式** (增加 `level` 和 `status`):
```json
{
  "score": 85,
  "level": "great",
  "feedback": "很好 🌟",
  "word_scores": [
    {"word": "The", "score": 95, "status": "good"},
    {"word": "elephant", "score": 55, "status": "weak"}
  ]
}
```

**字段说明**:
- `score`: 整数，0-100，整体发音评分
- `level`: 字符串，四级分类 (`excellent`/`great`/`good`/`keep_trying`)
- `feedback`: 字符串，儿童友好的中文反馈
- `word_scores`: 单词评分列表，每个单词包含 `word` (单词文本)、`score` (0-100)、`status` (`good` 或 `weak`)

### 5.2 SpeechAssessmentResult 更新

```python
@dataclass
class SpeechAssessmentResult:
    score: int                                    # 0-100 整体评分
    level: str = ""                               # 新增: excellent/great/good/keep_trying
    word_scores: List[WordScore] = field(default_factory=list)
    feedback: str = ""


@dataclass
class WordScore:
    word: str
    score: int  # 0-100
    status: str = "good"  # 新增: "good" 或 "weak"
```

### 5.3 错误处理

| 场景 | 行为 |
|------|------|
| 环境变量未配置 | `AzureSpeechAssessor.__init__()` 抛出 `ValueError`，提示缺少的配置项 |
| 音频过短 (< 1秒) | 返回 HTTP 400，提示"录音过短，请重新录制" |
| 音频过长 (> 60秒) | 返回 HTTP 400，提示"录音过长，请分段录制" |
| 音频格式不支持 | 先尝试后端转换为 WAV，转换失败则返回 HTTP 400 |
| Azure 服务不可用/超时 | 返回 HTTP 503，前端显示"评分服务暂时不可用，请稍后重试" |
| Azure API 错误 | 记录错误日志，返回 HTTP 500，前端显示"评分失败，请重试" |

### 5.4 重试机制

Azure Speech 服务可能因网络波动偶发失败，实现简单重试策略：
- 最多重试 3 次
- 使用指数退避：1秒、2秒、4秒
- 仅对网络错误和 5xx 响应重试，4xx 错误不重试

## 6. 代码变更范围

### 6.1 修改文件

#### 6.1.1 app/services/speech_assessment.py

**新增 AzureSpeechAssessor 类**:

```python
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
        if not self._key or not self._region:
            raise ValueError(
                "Azure Speech 评估器需要环境变量 AZURE_SPEECH_KEY 和 AZURE_SPEECH_REGION"
            )
        self._max_retries = 3
        self._audio_duration_min = 1.0   # 秒
        self._audio_duration_max = 60.0  # 秒

    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        """评估音频发音。

        流程:
        1. 验证音频时长
        2. 尝试直接提交 Azure (WebM 格式)
        3. 如失败，转换为 WAV 后重试
        4. 解析响应并映射为四级制评分

        Args:
            audio_bytes: 音频数据 (WebM/Opus 格式)
            text: 参考文本 (用户应该读的内容)

        Returns:
            SpeechAssessmentResult 包含评分和单词级反馈

        Raises:
            ValueError: 音频时长不合法
            RuntimeError: Azure 服务调用失败
        """
        ...

    def _validate_audio_duration(self, audio_bytes: bytes) -> float:
        """验证音频时长，返回时长（秒）。"""
        ...

    def _convert_to_wav(self, audio_bytes: bytes) -> bytes:
        """将音频转换为 16kHz WAV 格式。"""
        ...

    def _map_score_to_level(self, score: int) -> tuple[str, str]:
        """将分数映射为四级制等级和反馈。

        Returns:
            (level, feedback) 元组
        """
        ...

    def _map_word_score(self, score: int) -> str:
        """将单词分数映射为状态。"""
        return "good" if score >= 70 else "weak"
```

**修改 get_assessor()**:

```python
def get_assessor() -> SpeechAssessor:
    """根据环境变量 SPEECH_ASSESSOR 返回对应实现。"""
    provider = os.environ.get("SPEECH_ASSESSOR", "mock").lower()
    if provider == "aliyun":
        return AliyunSpeechAssessor()
    if provider == "azure":
        return AzureSpeechAssessor()
    return MockSpeechAssessor()
```

#### 6.1.2 .env.example（新增示例）

```bash
# Azure Speech Service 配置
SPEECH_ASSESSOR=azure
AZURE_SPEECH_KEY=your-key-here
AZURE_SPEECH_REGION=eastasia
```

### 6.2 测试要求

1. **单元测试**: `tests/test_speech_assessment.py`
   - 测试 Azure 评估器配置加载
   - 测试评分映射逻辑
   - 测试错误处理

2. **集成测试**: 手动验证
   - 配置真实 Azure 密钥测试端到端流程
   - 验证音频格式兼容性

## 7. 依赖项

```
azure-cognitiveservices-speech>=1.35.0
```

## 8. 部署清单

- [ ] 安装 azure-cognitiveservices-speech 包
- [ ] 配置环境变量 AZURE_SPEECH_KEY 和 AZURE_SPEECH_REGION
- [ ] 设置 SPEECH_ASSESSOR=azure
- [ ] 验证 /api/raz/assess 端点正常工作
- [ ] 检查日志确认使用 Azure 评估器

## 9. 未来扩展

- **音素级反馈**: Azure 支持返回每个单词的音素评分，可用于更精细的发音指导
- **流利度评估**: 可添加语速、停顿等流利度指标
- **缓存机制**: 对相同句子的评估结果进行缓存，减少 API 调用

---

**决策记录**:
- 音频格式: 先尝试直接传递 WebM，不兼容时增加转换逻辑
- 评分等级: 四级制（excellent/great/good/keep_trying）
- 单词阈值: 70 分作为 good/weak 分界
- 数据格式: 详细版，包含完整单词评分列表
