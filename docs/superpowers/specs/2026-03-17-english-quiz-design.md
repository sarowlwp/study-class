# 英语抽测卡功能设计文档

## 概述

新增英语单词抽测卡功能模块，支持小学英语单词的听、说、读、写练习。参考 Duolingo 卡片设计风格，提供三种抽测模式。数据存储方式与现有汉字抽测卡保持一致，使用 Markdown 文件。

## 目标

1. 支持小学英语单词的复习评测
2. 提供听音选词、看词选义、看义选词三种模式
3. 复用现有记录存储和掌握度统计逻辑
4. 保持与汉字抽测卡一致的用户体验

## 非目标

1. 暂不支持语音识别评测（看词发音模式）
2. 暂不支持主题分类，仅按年级+单元组织
3. 暂不支持自定义单词本

## 数据模型

### EnglishWord

```python
@dataclass
class EnglishWord:
    """英语单词数据模型"""
    word: str                    # 英文单词
    meaning: str                 # 中文释义
    phonetic: Optional[str] = None      # 音标（可选）
    example: Optional[str] = None       # 例句（英文，可选）
    example_cn: Optional[str] = None    # 例句翻译（可选）
    lesson: str = ""             # 所属单元
    semester: str = ""           # 年级/册别
    image_keyword: Optional[str] = None # 图片搜索关键词

    def to_dict(self, include_status: bool = False) -> dict:
        """转换为字典"""
        result = {
            "word": self.word,
            "meaning": self.meaning,
            "phonetic": self.phonetic,
            "example": self.example,
            "example_cn": self.example_cn,
            "lesson": self.lesson,
            "semester": self.semester,
            "image_keyword": self.image_keyword,
        }
        return result
```

### EnglishQuizMode

```python
class EnglishQuizMode(str, Enum):
    AUDIO_TO_WORD = "audio_to_word"      # 听音选词
    WORD_TO_MEANING = "word_to_meaning"  # 看词选义
    MEANING_TO_WORD = "meaning_to_word"  # 看义选词
```

### EnglishQuizRecord

```python
@dataclass
class EnglishQuizRecord:
    """英语评测记录"""
    word: str
    meaning: str
    lesson: str
    mode: EnglishQuizMode
    result: ResultType           # mastered / fuzzy / not_mastered
    timestamp: datetime
```

### EnglishQuizSessionState

```python
@dataclass
class EnglishQuizSessionState:
    """英语抽测会话状态"""
    session_id: str
    created_at: datetime
    total: int
    lessons: List[str]
    current_index: int
    words: List[dict]            # 抽测单词列表
    records: List[EnglishQuizRecord]
    completed: bool
```

## 数据文件格式

### 单词数据文件

路径：`data/english/{semester_id}.md`

```markdown
# 三年级上册

## Unit 1: Hello

| 单词 | 音标 | 释义 | 例句 | 例句翻译 | 图片关键词 |
|------|------|------|------|----------|-----------|
| hello | /həˈləʊ/ | 你好 | Hello, I'm Tom. | 你好，我是汤姆。 | hello |
| name | /neɪm/ | 名字 | My name is Amy. | 我的名字叫艾米。 | name |

## Unit 2: Colours

| 单词 | 音标 | 释义 | 例句 | 例句翻译 | 图片关键词 |
|------|------|------|------|----------|-----------|
| red | /red/ | 红色 | I like red. | 我喜欢红色。 | red |
| blue | /bluː/ | 蓝色 | The sky is blue. | 天空是蓝色的。 | blue |
```

### 评测记录文件

路径：`data/records/english-{YYYY-MM-DD}.md`

```markdown
# 2026-03-17 英语评测记录

## 统计
- 总数: 20
- 掌握: 15
- 模糊: 3
- 未掌握: 2
- 正确率: 75.0%

## 评测结果
| 单词 | 释义 | 课文 | 模式 | 结果 | 时间 |
|------|------|------|------|------|------|
| hello | 你好 | Unit 1: Hello | audio_to_word | mastered | 19:30:15 |
| name | 名字 | Unit 1: Hello | word_to_meaning | fuzzy | 19:31:22 |
```

## 页面路由

| 路由 | 方法 | 功能描述 |
|------|------|----------|
| `/english` | GET | 英语抽测首页，选择年级、单元、数量 |
| `/english/quiz` | GET | 抽测进行中页面，需传 `session` 参数 |
| `/english/result` | GET | 抽测结果页面，需传 `session` 参数 |
| `/english/mistakes` | GET | 英语错词本 |

## API 路由

| 路由 | 方法 | 功能描述 |
|------|------|----------|
| `/api/english/semesters` | GET | 获取所有年级列表 |
| `/api/english/lessons` | GET | 获取指定年级的单元列表，参数 `semester` |
| `/api/english/quiz/start` | POST | 开始抽测，创建会话 |
| `/api/english/quiz/session/{session_id}` | GET | 获取会话状态 |
| `/api/english/quiz/submit` | POST | 提交答案 |
| `/api/english/quiz/finish` | POST | 完成抽测，保存记录 |
| `/api/english/mistakes` | GET | 获取错词列表 |
| `/api/english/stats` | GET | 获取学习统计 |

## 前端交互设计

### 模式 A：听音选词 (Audio → Word)

```
┌────────────────────────────────────────┐
│  🔊 [大播放按钮]                        │
│                                         │
│  "听读音，选择正确的单词"                │
│                                         │
│  ┌────────┐ ┌────────┐ ┌────────┐      │
│  │  cat   │ │  dog   │ │  pig   │      │
│  │ /kæt/  │ │ /dɒɡ/  │ │ /pɪɡ/  │      │
│  └────────┘ └────────┘ └────────┘      │
│                                         │
│  [重新播放]                             │
└────────────────────────────────────────┘
```

交互流程：
1. 页面加载后显示大播放按钮，需要用户点击播放（浏览器限制自动播放）
2. 播放读音后，显示 3-4 个选项卡片（包含音标）
3. 用户点击选择后，显示正确/错误反馈
4. 正确答案高亮显示，错误答案标记
5. 自动进入下一题或显示"下一题"按钮

**注意**：由于浏览器自动播放限制，音频不会自动播放，需要用户点击播放按钮。

### 模式 B：看词选义 (Word → Meaning)

```
┌────────────────────────────────────────┐
│                                         │
│           c a t                         │
│          /kæt/                          │
│                                         │
│  ┌──────────────────────────┐          │
│  │          猫              │          │
│  └──────────────────────────┘          │
│  ┌──────────────────────────┐          │
│  │          狗              │          │
│  └──────────────────────────┘          │
│  ┌──────────────────────────┐          │
│  │          猪              │          │
│  └──────────────────────────┘          │
│                                         │
└────────────────────────────────────────┘
```

交互流程：
1. 页面中央显示英文单词和音标
2. 下方显示 3-4 个中文释义选项
3. 用户点击选择后显示反馈

### 模式 C：看义选词 (Meaning → Word)

```
┌────────────────────────────────────────┐
│                                         │
│  ┌──────────────────────────────┐      │
│  │     [猫的图片]               │      │
│  │    (或显示 "猫" 文字)        │      │
│  └──────────────────────────────┘      │
│                                         │
│  ┌────────┐ ┌────────┐ ┌────────┐      │
│  │  cat   │ │  dog   │ │  pig   │      │
│  └────────┘ └────────┘ └────────┘      │
│                                         │
└────────────────────────────────────────┘
```

交互流程：
1. 显示图片或中文释义
2. 下方显示 3-4 个英文单词选项
3. 用户点击选择后显示反馈

### 选项生成逻辑

- 选项数量：根据单词数量动态决定，最少 3 个，最多 4 个
- 干扰项来源：从同一单元或同一年级的其他单词中随机选择
- 选项顺序：每次随机打乱

**确保干扰项有效性**：
1. 干扰项不能与正确答案相同（word 和 meaning 都不同）
2. 干扰项之间也不能重复
3. 如果可用单词不足，允许重复显示（但标记为不同选项）

```python
def _generate_options(
    self,
    correct: EnglishWord,
    all_words: List[EnglishWord],
    option_count: int = 4
) -> List[Dict]:
    """生成选项，包含正确答案和干扰项"""
    # 过滤掉正确答案的候选干扰项
    distractors = [
        w for w in all_words
        if w.word != correct.word and w.meaning != correct.meaning
    ]

    # 随机选择干扰项
    selected_count = min(option_count - 1, len(distractors))
    selected = random.sample(distractors, selected_count) if distractors else []

    # 构建选项列表
    options = [
        {"word": correct.word, "meaning": correct.meaning, "phonetic": correct.phonetic, "is_correct": True}
    ]
    for word in selected:
        options.append({
            "word": word.word,
            "meaning": word.meaning,
            "phonetic": word.phonetic,
            "is_correct": False
        })

    # 随机打乱顺序
    random.shuffle(options)
    return options
```

### 语音播放

使用 Web Speech API：

```javascript
function speakWord(word) {
    const utterance = new SpeechSynthesisUtterance(word);
    utterance.lang = 'en-US';
    utterance.rate = 0.8;  // 稍慢语速，适合儿童
    utterance.pitch = 1.0;
    speechSynthesis.speak(utterance);
}
```

### 图片展示

**注意**：Unsplash Source API 已废弃，第一版暂不使用外部图片服务。

实现方案：
1. **第一版**：使用占位图服务 `https://via.placeholder.com/300x200?text={word}` 或显示 emoji/文字代替
2. **后续扩展**：如需真实图片，可使用 Unsplash API（需要注册获取 API key）或准备本地图片资源

前端实现时预留图片展示区域，当前版本显示单词对应的 emoji 或首字母大写展示。

## 文件结构

```
app/
├── models/
│   ├── __init__.py
│   ├── character.py
│   └── english_word.py          # 新增
├── services/
│   ├── __init__.py
│   ├── character_service.py
│   ├── quiz_service.py
│   ├── record_service.py
│   ├── english_service.py       # 新增
│   └── english_quiz_service.py  # 新增
├── routers/
│   ├── __init__.py
│   ├── pages.py
│   ├── api.py
│   └── english.py               # 新增
└── templates/
    ├── base.html
    ├── index.html
    ├── quiz.html
    ├── english/
    │   ├── index.html           # 新增：英语首页
    │   ├── quiz.html            # 新增：英语抽测中
    │   ├── result.html          # 新增：英语结果页
    │   └── mistakes.html        # 新增：英语错词本

data/
├── characters/
├── english/                     # 新增
│   ├── grade3-autumn.md
│   └── grade3-spring.md
└── records/
    ├── 2026-03-17.md
    └── english-2026-03-17.md    # 新增
```

## 配置更新

### app/config.py

添加英语数据目录配置：

```python
# 在现有配置后添加
ENGLISH_DIR = DATA_DIR / "english"
ENGLISH_DIR.mkdir(parents=True, exist_ok=True)
```

## 路由注册

### app/main.py

添加英语路由：

```python
from app.routers import english

# 在现有路由后添加
app.include_router(english.router)
```

## 导航集成

### app/templates/index.html

在主页面导航栏添加英语抽测入口：

```html
<!-- 在现有导航项后添加 -->
<a href="/english" class="nav-item">
    🔤 英语抽测
</a>
```

## 核心类设计

### EnglishService

```python
class EnglishService:
    """英语单词数据管理服务"""

    def get_semesters(self) -> List[Dict]:
        """获取所有年级列表"""

    def get_lessons(self, semester_id: str) -> List[Dict]:
        """获取指定年级的单元列表"""

    def get_words(self, semester_id: str, lessons: Optional[List[str]] = None) -> List[EnglishWord]:
        """获取单词列表"""

    def get_all_words(self) -> List[EnglishWord]:
        """获取所有单词"""
```

### EnglishQuizService

```python
class EnglishQuizService:
    """英语抽测服务"""

    _sessions: Dict[str, EnglishQuizSessionState] = {}

    def generate_quiz(
        self,
        semester_id: str,
        lessons: List[str],
        count: int,
        mode_mix: float = 0.33
    ) -> EnglishQuizSessionState:
        """生成抽测会话"""

    def get_session(self, session_id: str) -> Optional[EnglishQuizSessionState]:
        """获取会话状态"""

    def submit_answer(self, session_id: str, index: int, answer: str) -> Dict:
        """提交答案，返回是否正确及正确答案"""

    def finish_quiz(self, session_id: str) -> Dict:
        """完成抽测，保存记录"""

    def _generate_options(self, word: EnglishWord, all_words: List[EnglishWord], count: int) -> List[Dict]:
        """生成干扰选项"""
```

### EnglishRecordService (扩展)

复用现有 `RecordService`，新增英语相关方法：

```python
class RecordService:
    # 现有方法...

    def save_english_records(self, record_date: date, records: List[EnglishQuizRecord]):
        """保存英语评测记录"""

    def get_english_mastery_status(self, word: str, lesson: str) -> str:
        """获取单词掌握状态"""

    def get_english_mistakes(self) -> List[Dict]:
        """获取英语错词本"""
```

## 错误处理

### 1. 无可用单词
如果选择的单元没有单词数据，显示友好提示：
```
┌────────────────────────────────────────┐
│                                         │
│     😕 该单元暂无单词数据                │
│                                         │
│     请选择其他单元或联系管理员添加数据   │
│                                         │
│     [返回首页]                          │
│                                         │
└────────────────────────────────────────┘
```

### 2. 浏览器不支持语音
检测 Web Speech API 支持情况，不支持时：
- 隐藏"听音选词"模式选项
- 在相关页面显示提示："您的浏览器不支持语音播放，请使用 Chrome 或 Edge 浏览器"

### 3. 会话过期
返回 404，前端引导用户重新开始：
```
┌────────────────────────────────────────┐
│                                         │
│     ⏰ 会话已过期                        │
│                                         │
│     抽测会话已过期，请重新开始           │
│                                         │
│     [返回英语首页]                      │
│                                         │
└────────────────────────────────────────┘
```

## 性能考虑

1. 单词数据缓存在 `EnglishService._cache` 中，避免重复读取文件
2. 会话状态存储在内存中
3. 图片使用占位图服务，不占用本地存储

### 会话清理机制

由于会话存储在内存中，需要定期清理过期会话避免内存泄漏：

```python
def _cleanup_expired_sessions(self):
    """清理过期会话（24小时）"""
    now = datetime.now()
    expired = [
        sid for sid, session in self._sessions.items()
        if (now - session.created_at).total_seconds() > 86400
    ]
    for sid in expired:
        del self._sessions[sid]
```

在 `get_session` 和 `generate_quiz` 方法中调用清理逻辑。

## 测试策略

1. **单元测试**：测试 `EnglishService` 的文件解析逻辑
2. **单元测试**：测试 `EnglishQuizService` 的选项生成逻辑
3. **集成测试**：测试 API 端点的完整流程
4. **手动测试**：验证语音播放和图片显示效果

## 后续扩展

1. 支持语音识别评测模式（看词发音）
2. 支持自定义单词本
3. 支持单词难度分级
4. 支持学习进度图表展示
5. 支持导出单词卡片 PDF
