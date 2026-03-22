# RAZ 英语跟读练习功能设计文档

**日期**: 2026-03-21
**状态**: 待实现

---

## 1. 功能概述

为现有小学学习工具新增 RAZ 英语分级阅读跟读练习模块，帮助小学生通过语音跟读和发音评测的方式学习 RAZ 英语课程。

**核心功能**：
- 浏览 RAZ 分级书库（Level aa~Z2），家长手动切换当前 Level
- 观看整本书视频预览
- 逐句跟读练习：播放页面参考音频 → 学生录音 → AI 发音评分
- 每日任务：手动设定句数 或 智能推荐
- 练习记录以 Markdown 文件存储，按日期归档

---

## 2. 数据结构

### 2.1 书库目录结构

```
data/raz/
  level-a/
    the-big-red-barn/
      book.json
      page01.pdf
      page01.mp3
      page02.pdf
      page02.mp3
      full.mp4          # 整本书视频（可选）
      ...
  level-b/
    ...

data/raz-records/
  2026-03-21.md         # 当日练习记录

data/raz-config.json    # 全局配置（当前 Level、每日任务设置）
```

### 2.2 book.json 格式

```json
{
  "id": "the-big-red-barn",
  "title": "The Big Red Barn",
  "level": "a",
  "video": "full.mp4",
  "pages": [
    {
      "page": 1,
      "pdf": "page01.pdf",
      "audio": "page01.mp3",
      "sentences": [
        "This is a big red barn.",
        "Animals live here."
      ]
    }
  ]
}
```

### 2.3 练习记录格式（Markdown）

文件路径：`data/raz-records/YYYY-MM-DD.md`

```markdown
# RAZ 练习记录 2026-03-21

## The Big Red Barn (Level A)

| 页码 | 句子 | 评分 | 时间 |
|------|------|------|------|
| 1 | This is a big red barn. | 85 | 09:15:00 |
| 1 | Animals live here. | 92 | 09:16:10 |
| 2 | The cow says moo. | 78 | 09:17:30 |
```

### 2.4 全局配置（raz-config.json）

```json
{
  "current_level": "a",
  "daily_mode": "manual",
  "daily_count": 10,
  "current_session": {
    "book_id": "the-big-red-barn",
    "page": 2,
    "sentence_index": 1
  }
}
```

`daily_mode`: `"manual"` | `"smart"`

`current_session` 记录最近一次练习位置，刷新页面后可从断点续练。`book_id` 在整个书库中全局唯一（使用目录名，格式 `level-{x}/{dir_name}`，如 `level-a/the-big-red-barn`）。

---

## 3. 学习流程

```
书库首页（/raz）
  └── 选书 → 书详情页（/raz/book/{book_id}）
        ├── [可选] 播放整本视频
        └── 开始练习 → 逐句练习页（/raz/practice/{book_id}）
              └── 完成今日任务 → 进度页（/raz/progress）
```

### 逐句练习流程（每句）

每页有一个音频文件（`page0X.mp3`），包含该页全部内容的朗读。逐句练习时，每次均播放**整页音频**作为参考示范，学生根据高亮句子录音朗读该句。

1. 展示当前页 PDF
2. 高亮当前句文本
3. 点击播放 → 播放该页整段 `page0X.mp3`（作为参考示范）
4. 点击录音 → 浏览器采集音频（浏览器 MediaRecorder 默认格式 WebM，服务端转 WAV 后提交评测）
5. 停止录音 → 提交给发音评测服务（附带目标句子文本）
6. 显示评分结果（优 ≥90 / 良 ≥70 / 需加油 <70）
7. 操作：[下一句] / [重新录] / [跳过]
8. 本页所有句子完成 → 进入下一页

### 每日任务

- **手动模式**：家长设定每天练习 N 句，完成后显示"今日任务完成"，仍可继续
- **智能推荐**：`近7天平均完成句数 × 完成率`，无历史时默认 10 句

**每日进度计算**：实时扫描 `data/raz-records/YYYY-MM-DD.md`，统计当天行数作为已完成句数。同一句子多次练习均追加记录（保留历史尝试），统计时以行数为准（重录也计入完成）。记录文件格式错误（非标准 Markdown 表格）时跳过该行，不崩溃。

---

## 4. 后端架构

### 4.1 新增文件

```
app/
  routers/
    raz.py
  services/
    raz_service.py          # 书库扫描、book.json 解析、进度读写
    raz_practice_service.py # 练习会话管理、每日任务计算
    speech_assessment.py    # 发音评测抽象层 + 各实现
  templates/
    raz/
      index.html            # 书库首页
      book.html             # 书详情页
      practice.html         # 逐句练习页
      progress.html         # 进度总览
```

### 4.2 页面路由

| 路由 | 说明 |
|------|------|
| `GET /raz` | 书库首页 |
| `GET /raz/book/{book_id}` | 书详情页 |
| `GET /raz/practice/{book_id}` | 练习页 |
| `GET /raz/progress` | 进度总览 |

### 4.3 API 路由

| 路由 | 说明 |
|------|------|
| `GET /api/raz/books` | 获取当前 Level 书库列表 |
| `GET /api/raz/book/{book_id}` | 获取书的详情（含所有页句子） |
| `POST /api/raz/assess` | 提交录音评测（接收 audio + text） |
| `GET /api/raz/progress` | 获取练习进度统计 |
| `GET /api/raz/config` | 获取全局配置 |
| `POST /api/raz/config` | 更新全局配置（Level、每日任务） |
| `GET /raz/static/{level}/{book}/{file}` | 提供 PDF/MP3/MP4 静态文件（路径参数严格校验，禁止 `..` 及非法字符，防止路径穿越攻击） |

---

## 5. 发音评测抽象层

### 5.1 接口定义

```python
# app/services/speech_assessment.py

from dataclasses import dataclass, field
from typing import Protocol, List

@dataclass
class WordScore:
    word: str
    score: int  # 0-100

@dataclass
class SpeechAssessmentResult:
    score: int              # 0-100，句子整体评分
    word_scores: List[WordScore] = field(default_factory=list)
    feedback: str = ""      # 简短反馈文字

class SpeechAssessor(Protocol):
    async def assess(self, audio_bytes: bytes, text: str) -> SpeechAssessmentResult:
        ...
```

### 5.2 实现类

| 类名 | 说明 |
|------|------|
| `AliyunSpeechAssessor` | 阿里云智能语音交互发音评测 |
| `AzureSpeechAssessor` | Azure Cognitive Services（预留） |
| `MockSpeechAssessor` | 本地随机评分，开发/测试用 |

### 5.3 配置切换

通过环境变量 `SPEECH_ASSESSOR` 选择实现：

```bash
SPEECH_ASSESSOR=aliyun   # 默认
SPEECH_ASSESSOR=azure
SPEECH_ASSESSOR=mock     # 开发用
```

应用启动时根据配置注入对应实现，业务代码依赖 `SpeechAssessor` Protocol，不感知具体实现。

### 5.4 阿里云配置

```bash
ALIYUN_ACCESS_KEY_ID=...
ALIYUN_ACCESS_KEY_SECRET=...
ALIYUN_NLS_APP_KEY=...
```

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|----------|
| 录音权限被拒 | 提示开启麦克风，不阻塞页面 |
| 录音过短（< 0.5s） | 提示"请说长一点"，不提交 |
| 评测 API 超时/失败 | 提示"评分失败"，可重试或跳过 |
| `book.json` 缺失/格式错误 | 书库页跳过该书，记录日志 |
| PDF/音频文件不存在 | 练习页显示占位提示，不崩溃 |
| 记录文件格式损坏 | 跳过格式错误的行，不影响读取其他行 |
| 当日记录文件不存在 | 视为今日已完成 0 句，正常继续 |

---

## 7. 不在本期范围内

- 整页测试（先只做逐句练习）
- 用户认证（与现有项目一致，单用户本地应用）
- 自动 Level 升级（家长手动切换）
- 音频时间轴标注工具（可后续迭代）
