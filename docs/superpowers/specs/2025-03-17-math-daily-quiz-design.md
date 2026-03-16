# 数学每日小测功能设计文档

**创建日期**: 2025-03-17
**状态**: 待实现

---

## 1. 功能概述

为语文学习小工具新增数学每日小测模块，支持生成 10-20 道可打印的数学练习题，覆盖小学 1-6 年级常用口算题型。

## 2. 用户流程

```
首页 (/)
  └── 点击"数学每日小测"卡片
      └── 配置页面 (/math-quiz)
          ├── 选择年级 (1-6)
          ├── 选择题目数量 (10-20)
          ├── 选择题型 (10种，可多选)
          ├── 是否显示答案 (复选框)
          └── 点击生成
              └── 预览页面 (/math-quiz/preview)
                  └── 浏览器打印 / 返回修改
```

## 3. 页面设计

### 3.1 首页入口

在 `index.html` 的 Quick Links 区域新增第四个卡片：

```html
<a href="/math-quiz" class="bg-white rounded-xl shadow p-6 hover:shadow-lg transition flex items-center space-x-4">
    <span class="text-4xl">📐</span>
    <div>
        <h3 class="font-bold text-gray-800">数学每日小测</h3>
        <p class="text-sm text-gray-500">生成可打印的数学练习题</p>
    </div>
</a>
```

### 3.2 配置页面 (/math-quiz)

**布局结构**：
- 页面标题：数学每日小测配置
- 年级选择：单选按钮组 1-6 年级，默认 3 年级
- 题目数量：滑块 10-20，默认 15
- 题型选择：10 个复选框，按年级自动勾选默认值
- 显示答案：复选框，默认不勾选
- 生成按钮：跳转预览页

**年级默认题型映射**：

| 年级 | 默认题型 | 数字范围 |
|------|----------|----------|
| 1年级 | 1, 2 | 0-20 |
| 2年级 | 1, 2, 3, 6 | 0-100，表内乘除 |
| 3年级 | 1, 2, 3, 4, 6, 7 | 0-1000 |
| 4年级 | 3, 4, 5, 6, 7, 8, 9 | 大数，小数初步 |
| 5年级 | 5, 6, 7, 8, 9, 10 | 小数、分数 |
| 6年级 | 全部 | 综合 |

### 3.3 预览页面 (/math-quiz/preview)

**URL 参数**：`?grade=3&count=15&types=1,2,3&answers=0`

**页面布局**：
```
┌─────────────────────────────────────────┐
│           数学每日小测                    │
│           三年级    2025年3月17日         │
├─────────────────────────────────────────┤
│                                         │
│  1. 23 + 45 = ____    2. 68 - 24 = ____ │
│                                         │
│  3. 38 + 47 = ____    4. 52 - 29 = ____ │
│                                         │
│  ... (两栏排列)                          │
│                                         │
├─────────────────────────────────────────┤
│              【打印按钮】                 │
└─────────────────────────────────────────┘
```

**打印样式**：
- 使用 `@media print` 隐藏按钮和导航
- 题目区域占满 A4 纸
- 可选：答案单独一页或底部小字显示

## 4. 数据结构

### 4.1 请求模型

```python
from pydantic import BaseModel, Field
from typing import List

class MathQuizRequest(BaseModel):
    """生成数学小测请求"""
    grade: int = Field(..., ge=1, le=6, description="年级 1-6")
    count: int = Field(15, ge=10, le=20, description="题目数量 10-20")
    types: List[int] = Field(..., description="题型列表 1-10")
    show_answers: bool = Field(False, description="是否显示答案")

class MathQuizDefaultsRequest(BaseModel):
    """获取年级默认题型请求"""
    grade: int = Field(..., ge=1, le=6)
```

### 4.2 响应模型

```python
class MathProblem(BaseModel):
    """单道题目"""
    id: int = Field(..., description="题号 1-N")
    type: int = Field(..., description="题型编号 1-10")
    type_name: str = Field(..., description="题型名称")
    question: str = Field(..., description="题目文本")
    answer: str = Field(..., description="正确答案")
    work_lines: int = Field(1, description="答题需要行数")

class MathQuizResponse(BaseModel):
    """生成响应"""
    problems: List[MathProblem]
    summary: dict = Field(..., description="题型分布统计")
    grade: int
    count: int
```

### 4.3 题型定义

```python
PROBLEM_TYPES = {
    1: {"name": "基本加减", "desc": "不进位/不退位"},
    2: {"name": "进位退位", "desc": "进位加法/退位减法"},
    3: {"name": "整十整百", "desc": "整十/整百加减"},
    4: {"name": "多位数加减", "desc": "两位数/三位数"},
    5: {"name": "简便计算", "desc": "凑整法/拆分法"},
    6: {"name": "乘除口诀", "desc": "表内乘除法"},
    7: {"name": "多步混合", "desc": "加减乘除混合"},
    8: {"name": "括号运算", "desc": "带小括号的运算"},
    9: {"name": "分数小数", "desc": "分数/小数计算"},
    10: {"name": "巧算估算", "desc": "规律/估算专项"},
}
```

## 5. API 设计

### 5.1 端点列表

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/math-quiz` | 配置页面 |
| GET | `/math-quiz/preview` | 预览页面（带查询参数）|
| POST | `/api/math/quiz/generate` | 生成题目 |
| GET | `/api/math/quiz/defaults` | 获取年级默认题型 |

### 5.2 生成题目 API

**请求**：
```json
POST /api/math/quiz/generate
{
    "grade": 3,
    "count": 15,
    "types": [1, 2, 3, 6],
    "show_answers": false
}
```

**响应**：
```json
{
    "problems": [
        {
            "id": 1,
            "type": 1,
            "type_name": "基本加减",
            "question": "23 + 45 = ____",
            "answer": "68",
            "work_lines": 1
        },
        {
            "id": 2,
            "type": 2,
            "type_name": "进位退位",
            "question": "38 + 47 = ____",
            "answer": "85",
            "work_lines": 1
        }
    ],
    "summary": {
        "1": 4,
        "2": 4,
        "3": 3,
        "6": 4
    },
    "grade": 3,
    "count": 15
}
```

## 6. 题目生成规则

### 6.1 数字范围配置

```python
GRADE_RANGES = {
    1: {"add_sub": (0, 20), "mul_div": None},
    2: {"add_sub": (0, 100), "mul_div": (1, 9)},
    3: {"add_sub": (0, 1000), "mul_div": (1, 9)},
    4: {"add_sub": (0, 10000), "mul_div": (1, 12), "decimal": True},
    5: {"add_sub": (0, 100000), "mul_div": (1, 20), "fraction": True},
    6: {"add_sub": (0, 1000000), "mul_div": (1, 100), "fraction": True, "decimal": True},
}
```

### 6.2 题型生成逻辑

**类型 1 - 基本加减**：
- 生成两个随机数，和/差不进位不退位
- 例：`23 + 45`, `68 - 24`

**类型 2 - 进位退位**：
- 个位数相加 ≥10 或个位被减数 < 减数个位
- 例：`38 + 47`, `52 - 29`

**类型 3 - 整十整百**：
- 数字为 10/100 的倍数，或结果凑整
- 例：`120 + 80`, `300 - 90`

**类型 4 - 多位数加减**：
- 两位数或三位数混合
- 例：`145 + 267`, `523 - 178`

**类型 5 - 简便计算**：
- 接近整十/整百的数
- 例：`99 + 36`, `198 - 99`, `25 + 75`

**类型 6 - 乘除口诀**：
- 表内乘除，九九乘法范围内
- 例：`7 × 8`, `56 ÷ 7`

**类型 7 - 多步混合**：
- 2-3 步运算，无括号
- 例：`72 ÷ 9 × 5`, `48 + 36 - 20`

**类型 8 - 括号运算**：
- 包含小括号改变优先级
- 例：`120 - (45 + 28)`, `8 × (12 - 3)`

**类型 9 - 分数小数**：
- 同分母分数或简单小数
- 例：`3/4 + 1/4`, `0.7 + 0.8`, `2.5 × 4`

**类型 10 - 巧算估算**：
- 特殊技巧或估算
- 例：`25 × 4`, `199 × 5`, `398 + 503 ≈ ?`

### 6.3 混排策略

1. 根据 `count` 和 `types` 均匀分配各题型数量
2. 每个题型独立生成对应数量的题目
3. 合并后随机打乱顺序
4. 重新编号 1-N

## 7. 项目结构

```
app/
├── routers/
│   ├── __init__.py
│   ├── pages.py              # 添加页面路由
│   └── math_quiz.py          # 新增: API 路由
├── services/
│   ├── __init__.py
│   └── math_generator.py     # 新增: 题目生成服务
├── templates/
│   ├── base.html
│   ├── index.html            # 修改: 添加入口卡片
│   ├── math_quiz.html        # 新增: 配置页面
│   └── math_preview.html     # 新增: 预览页面
└── main.py                   # 修改: 注册新路由
```

## 8. 实现要点

### 8.1 题目唯一性
- 同一套题内避免重复题目
- 使用集合记录已生成的 (type, a, b) 组合

### 8.2 答案计算
- 每道题生成时同步计算正确答案
- 使用 Python `eval()` 或手动计算确保准确性

### 8.3 打印优化
- CSS `@media print` 隐藏按钮和导航
- 页面设置 A4 尺寸
- 题目两栏排版，节省纸张

### 8.4 扩展性
- 题型生成函数独立，便于新增题型
- 年级配置集中管理，便于调整难度

## 9. 测试要点

- 各年级各题型能正常生成题目
- 题目数量严格符合请求（10-20道）
- 答案计算准确性
- 预览页面渲染正确
- 打印样式正常

## 10. 未来扩展（可选）

- 保存历史小测记录
- 支持 Word/PDF 导出
- 错题本功能
- 网页在线答题模式
