# 数学每日小测功能实现计划

> **For agentic workers:** REQUIRED: Use @superpowers:subagent-driven-development (if subagents available) or @superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现数学每日小测功能，支持生成 10-20 道可打印的数学练习题

**Architecture:** 后端 FastAPI 提供题目生成 API，前端 Jinja2 模板渲染配置页和预览页，浏览器原生打印

**Tech Stack:** Python 3.10+, FastAPI, Jinja2, Tailwind CSS

---

## 文件结构规划

```
app/
├── routers/
│   └── math_quiz.py          # 新增: API 路由
├── services/
│   └── math_generator.py     # 新增: 题目生成服务
├── templates/
│   ├── math_quiz.html        # 新增: 配置页面
│   └── math_preview.html     # 新增: 预览页面
├── models/
│   └── math_quiz.py          # 新增: Pydantic 模型
└── main.py                   # 修改: 注册新路由

tests/
├── test_math_generator.py    # 新增: 题目生成测试
└── test_math_api.py          # 新增: API 测试
```

---

## Chunk 1: 数据模型和常量定义

### Task 1.1: 创建 Pydantic 模型

**Files:**
- Create: `app/models/math_quiz.py`
- Test: `tests/test_math_models.py`

**Spec reference:** Section 4.1, 4.2, 4.3

- [ ] **Step 1: 编写模型测试**

```python
# tests/test_math_models.py
import pytest
from pydantic import ValidationError
from app.models.math_quiz import MathQuizRequest, MathProblem, PROBLEM_TYPES


def test_math_quiz_request_valid():
    """Test valid request creation"""
    req = MathQuizRequest(grade=3, count=15, types=[1, 2, 3], show_answers=True)
    assert req.grade == 3
    assert req.count == 15
    assert req.types == [1, 2, 3]
    assert req.show_answers is True


def test_math_quiz_request_defaults():
    """Test default values"""
    req = MathQuizRequest(grade=2, types=[1])
    assert req.count == 15
    assert req.show_answers is False


def test_math_quiz_request_grade_bounds():
    """Test grade must be 1-6"""
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=0, types=[1])
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=7, types=[1])


def test_math_quiz_request_count_bounds():
    """Test count must be 10-20"""
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=3, count=5, types=[1])
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=3, count=25, types=[1])


def test_math_problem_creation():
    """Test MathProblem model"""
    problem = MathProblem(
        id=1,
        type=1,
        type_name="基本加减",
        question="23 + 45 = ____",
        answer="68",
        work_lines=1
    )
    assert problem.id == 1
    assert problem.answer == "68"


def test_problem_types_defined():
    """Test all 10 problem types are defined"""
    assert len(PROBLEM_TYPES) == 10
    assert 1 in PROBLEM_TYPES
    assert 10 in PROBLEM_TYPES
    assert "name" in PROBLEM_TYPES[1]
    assert "desc" in PROBLEM_TYPES[1]
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
cd /Users/liuwenping/Documents/fliggy/study-class
pytest tests/test_math_models.py -v
```

**Expected:** FAIL - Module not found

- [ ] **Step 3: 实现数据模型**

```python
# app/models/math_quiz.py
from pydantic import BaseModel, Field
from typing import List


class MathQuizRequest(BaseModel):
    """生成数学小测请求"""
    grade: int = Field(..., ge=1, le=6, description="年级 1-6")
    count: int = Field(15, ge=10, le=20, description="题目数量 10-20")
    types: List[int] = Field(..., description="题型列表 1-10")
    show_answers: bool = Field(False, description="是否显示答案")


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


# 题型定义
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

# 年级默认题型映射
GRADE_DEFAULTS = {
    1: [1, 2],
    2: [1, 2, 3, 6],
    3: [1, 2, 3, 4, 6, 7],
    4: [3, 4, 5, 6, 7, 8, 9],
    5: [5, 6, 7, 8, 9, 10],
    6: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
}

# 年级数字范围配置
GRADE_RANGES = {
    1: {"add_sub": (0, 20), "mul_div": None},
    2: {"add_sub": (0, 100), "mul_div": (1, 9)},
    3: {"add_sub": (0, 1000), "mul_div": (1, 9)},
    4: {"add_sub": (0, 10000), "mul_div": (1, 12), "decimal": True},
    5: {"add_sub": (0, 100000), "mul_div": (1, 20), "fraction": True},
    6: {"add_sub": (0, 1000000), "mul_div": (1, 100), "fraction": True, "decimal": True},
}
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_math_models.py -v
```

**Expected:** All tests pass

- [ ] **Step 5: 提交**

```bash
git add app/models/math_quiz.py tests/test_math_models.py
git commit -m "feat(models): add math quiz pydantic models and constants

- Add MathQuizRequest, MathProblem, MathQuizResponse models
- Define PROBLEM_TYPES, GRADE_DEFAULTS, GRADE_RANGES
- Add comprehensive model validation tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: 题目生成服务

### Task 2.1: 实现基础题型生成器

**Files:**
- Create: `app/services/math_generator.py`
- Test: `tests/test_math_generator.py`

**Spec reference:** Section 6.1, 6.2

- [ ] **Step 1: 编写生成器基础测试**

```python
# tests/test_math_generator.py
import pytest
from app.services.math_generator import MathGenerator, ProblemCache


class TestProblemCache:
    def test_cache_adds_problem(self):
        cache = ProblemCache()
        assert cache.add(1, 23, 45)
        assert not cache.add(1, 23, 45)  # Duplicate

    def test_cache_different_types_same_numbers(self):
        cache = ProblemCache()
        assert cache.add(1, 23, 45)
        assert cache.add(2, 23, 45)  # Different type, same numbers ok


class TestBasicAdditionSubtraction:
    """Test Type 1: 基本加减"""

    def test_generate_no_carry_addition(self):
        gen = MathGenerator(grade=2)
        problem = gen._generate_type1()
        assert problem["type"] == 1
        assert "=" in problem["question"]
        # Verify no carry
        a, b = map(int, problem["question"].replace(" = ____", "").split(" + "))
        assert (a % 10) + (b % 10) < 10

    def test_generate_no_borrow_subtraction(self):
        gen = MathGenerator(grade=2)
        problem = gen._generate_type1()
        if "-" in problem["question"]:
            a, b = map(int, problem["question"].replace(" = ____", "").split(" - "))
            assert (a % 10) >= (b % 10)
            assert a >= b  # No negative results


class TestMathGeneratorBasic:
    def test_generator_creation(self):
        gen = MathGenerator(grade=3)
        assert gen.grade == 3
        assert gen.ranges["add_sub"] == (0, 1000)

    def test_generate_single_problem(self):
        gen = MathGenerator(grade=2)
        problem = gen.generate_problem(problem_type=1)
        assert "question" in problem
        assert "answer" in problem
        assert "type_name" in problem

    def test_generate_quiz(self):
        gen = MathGenerator(grade=3)
        quiz = gen.generate_quiz(count=10, types=[1, 2])
        assert len(quiz) == 10
        assert all(p["type"] in [1, 2] for p in quiz)

    def test_answer_correctness(self):
        gen = MathGenerator(grade=2)
        problem = gen.generate_problem(problem_type=1)
        # Parse and verify answer
        question = problem["question"].replace(" = ____", "").replace(" ", "")
        if "+" in question:
            a, b = map(int, question.split("+"))
            expected = str(a + b)
        elif "-" in question:
            a, b = map(int, question.split("-"))
            expected = str(a - b)
        assert problem["answer"] == expected
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_math_generator.py -v
```

**Expected:** FAIL - Module not found

- [ ] **Step 3: 实现题目生成器**

```python
# app/services/math_generator.py
import random
from typing import Dict, List, Set, Tuple, Optional
from app.models.math_quiz import MathProblem, PROBLEM_TYPES, GRADE_RANGES


class ProblemCache:
    """避免生成重复题目"""

    def __init__(self):
        self._cache: Set[Tuple[int, int, int]] = set()

    def add(self, problem_type: int, a: int, b: int) -> bool:
        """添加题目到缓存，返回是否为新题目"""
        key = (problem_type, a, b)
        if key in self._cache:
            return False
        self._cache.add(key)
        return True

    def clear(self):
        self._cache.clear()


class MathGenerator:
    """数学题目生成器"""

    def __init__(self, grade: int):
        self.grade = grade
        self.ranges = GRADE_RANGES.get(grade, GRADE_RANGES[3])
        self.cache = ProblemCache()

    def _get_random_number(self, min_val: int, max_val: int) -> int:
        """生成指定范围内的随机数"""
        return random.randint(min_val, max_val)

    def _safe_generate(self, generator_func, max_attempts: int = 100):
        """安全生成，避免无限循环"""
        for _ in range(max_attempts):
            result = generator_func()
            if result:
                return result
        # 如果缓存满了，清空缓存重试
        self.cache.clear()
        return generator_func()

    def _generate_type1_basic(self) -> Optional[Dict]:
        """类型1: 基本加减（不进位/不退位）"""
        min_val, max_val = self.ranges["add_sub"]

        # 50% 加法，50% 减法
        if random.random() < 0.5:
            # 加法，确保不进位
            a = self._get_random_number(min_val, max_val // 2)
            b = self._get_random_number(min_val, max_val - a)
            # 检查不进位
            if (a % 10) + (b % 10) >= 10:
                return None
            if not self.cache.add(1, a, b):
                return None
            return {
                "type": 1,
                "type_name": PROBLEM_TYPES[1]["name"],
                "question": f"{a} + {b} = ____",
                "answer": str(a + b),
                "work_lines": 1,
            }
        else:
            # 减法，确保不退位且结果非负
            a = self._get_random_number(min_val + 10, max_val)
            b = self._get_random_number(min_val, a)
            # 检查不退位
            if (a % 10) < (b % 10):
                return None
            if not self.cache.add(1, a, b):
                return None
            return {
                "type": 1,
                "type_name": PROBLEM_TYPES[1]["name"],
                "question": f"{a} - {b} = ____",
                "answer": str(a - b),
                "work_lines": 1,
            }

    def _generate_type2_carry_borrow(self) -> Optional[Dict]:
        """类型2: 进位加法/退位减法"""
        min_val, max_val = self.ranges["add_sub"]

        if random.random() < 0.5:
            # 进位加法
            a = self._get_random_number(10, max_val - 10)
            b = self._get_random_number(10, max_val - a)
            # 确保进位
            if (a % 10) + (b % 10) < 10:
                return None
            if not self.cache.add(2, a, b):
                return None
            return {
                "type": 2,
                "type_name": PROBLEM_TYPES[2]["name"],
                "question": f"{a} + {b} = ____",
                "answer": str(a + b),
                "work_lines": 1,
            }
        else:
            # 退位减法
            a = self._get_random_number(20, max_val)
            b = self._get_random_number(10, a - 1)
            # 确保退位
            if (a % 10) >= (b % 10):
                return None
            if not self.cache.add(2, a, b):
                return None
            return {
                "type": 2,
                "type_name": PROBLEM_TYPES[2]["name"],
                "question": f"{a} - {b} = ____",
                "answer": str(a - b),
                "work_lines": 1,
            }

    def _generate_type3_round_numbers(self) -> Optional[Dict]:
        """类型3: 整十整百加减"""
        # 生成整十或整百数
        if random.random() < 0.5:
            # 整十数
            a = random.randint(1, 20) * 10
            b = random.randint(1, 20) * 10
        else:
            # 整百数（高年级）
            multiplier = 10 if self.grade <= 3 else 100
            a = random.randint(1, 10) * multiplier
            b = random.randint(1, 10) * multiplier

        if random.random() < 0.5:
            if not self.cache.add(3, a, b):
                return None
            return {
                "type": 3,
                "type_name": PROBLEM_TYPES[3]["name"],
                "question": f"{a} + {b} = ____",
                "answer": str(a + b),
                "work_lines": 1,
            }
        else:
            if a < b:
                a, b = b, a
            if not self.cache.add(3, a, b):
                return None
            return {
                "type": 3,
                "type_name": PROBLEM_TYPES[3]["name"],
                "question": f"{a} - {b} = ____",
                "answer": str(a - b),
                "work_lines": 1,
            }

    def _generate_type4_multi_digit(self) -> Optional[Dict]:
        """类型4: 多位数加减"""
        min_val, max_val = self.ranges["add_sub"]
        # 根据年级调整位数
        if self.grade <= 2:
            a = random.randint(10, 99)
            b = random.randint(10, 99)
        else:
            a = random.randint(100, min(999, max_val))
            b = random.randint(100, min(999, max_val - a))

        if random.random() < 0.5:
            if not self.cache.add(4, a, b):
                return None
            return {
                "type": 4,
                "type_name": PROBLEM_TYPES[4]["name"],
                "question": f"{a} + {b} = ____",
                "answer": str(a + b),
                "work_lines": 1,
            }
        else:
            if a < b:
                a, b = b, a
            if not self.cache.add(4, a, b):
                return None
            return {
                "type": 4,
                "type_name": PROBLEM_TYPES[4]["name"],
                "question": f"{a} - {b} = ____",
                "answer": str(a - b),
                "work_lines": 1,
            }

    def _generate_type5_easy_calc(self) -> Optional[Dict]:
        """类型5: 简便计算（凑整）"""
        strategies = [
            # 接近100的加法
            lambda: (99, random.randint(1, 50)),
            lambda: (98, random.randint(2, 50)),
            # 接近100的减法
            lambda: (random.randint(100, 200), 99),
            lambda: (random.randint(100, 200), 98),
            # 凑整十
            lambda: (random.randint(1, 5) * 10, random.randint(1, 5) * 10),
            # 接近整百的数相加
            lambda: (random.randint(11, 20) * 10, random.randint(1, 9) * 10),
        ]

        strategy = random.choice(strategies)
        a, b = strategy()

        if random.random() < 0.5:
            if not self.cache.add(5, a, b):
                return None
            return {
                "type": 5,
                "type_name": PROBLEM_TYPES[5]["name"],
                "question": f"{a} + {b} = ____",
                "answer": str(a + b),
                "work_lines": 1,
            }
        else:
            if a < b:
                a, b = b, a
            if not self.cache.add(5, a, b):
                return None
            return {
                "type": 5,
                "type_name": PROBLEM_TYPES[5]["name"],
                "question": f"{a} - {b} = ____",
                "answer": str(a - b),
                "work_lines": 1,
            }

    def _generate_type6_multiply_divide(self) -> Optional[Dict]:
        """类型6: 乘除口诀"""
        if self.ranges["mul_div"] is None:
            # 低年级不支持乘除，退化为类型1
            return self._generate_type1_basic()

        mul_min, mul_max = self.ranges["mul_div"]

        if random.random() < 0.5:
            # 乘法
            a = random.randint(mul_min, mul_max)
            b = random.randint(1, 9)
            if not self.cache.add(6, a, b):
                return None
            return {
                "type": 6,
                "type_name": PROBLEM_TYPES[6]["name"],
                "question": f"{a} × {b} = ____",
                "answer": str(a * b),
                "work_lines": 1,
            }
        else:
            # 除法，确保整除
            b = random.randint(2, 9)
            result = random.randint(2, 12 if self.grade <= 3 else 20)
            a = b * result
            if not self.cache.add(6, a, b):
                return None
            return {
                "type": 6,
                "type_name": PROBLEM_TYPES[6]["name"],
                "question": f"{a} ÷ {b} = ____",
                "answer": str(result),
                "work_lines": 1,
            }

    def _generate_type7_mixed(self) -> Optional[Dict]:
        """类型7: 多步混合运算"""
        patterns = [
            # a + b - c
            lambda: (random.randint(10, 50), random.randint(10, 50), random.randint(5, 30)),
            # a - b + c
            lambda: (random.randint(50, 100), random.randint(10, 40), random.randint(10, 40)),
            # a * b / c (整除)
            lambda: self._make_multiply_divide(),
        ]

        pattern = random.choice(patterns)
        a, b, c = pattern()

        if isinstance(pattern(), tuple) and len(pattern()) == 3:
            # a * b / c
            if not self.cache.add(7, a, b * 100 + c):
                return None
            return {
                "type": 7,
                "type_name": PROBLEM_TYPES[7]["name"],
                "question": f"{a} × {b} ÷ {c} = ____",
                "answer": str(a * b // c),
                "work_lines": 2,
            }
        else:
            # 加减混合
            result = a + b - c
            if result < 0:
                a, c = c + 10, b  # 调整确保结果为正
                result = a + b - c
            if not self.cache.add(7, a, b * 100 + c):
                return None
            op1 = "+" if random.random() < 0.5 else "-"
            if op1 == "+":
                question = f"{a} + {b} - {c} = ____"
                answer = a + b - c
            else:
                question = f"{a} - {b} + {c} = ____"
                answer = a - b + c
            return {
                "type": 7,
                "type_name": PROBLEM_TYPES[7]["name"],
                "question": question,
                "answer": str(answer),
                "work_lines": 2,
            }

    def _make_multiply_divide(self):
        """生成整除的乘除组合"""
        c = random.randint(2, 5)
        b = random.randint(2, 5)
        a = c * b
        return (a, b, c)

    def _generate_type8_parentheses(self) -> Optional[Dict]:
        """类型8: 括号运算"""
        # a - (b + c) 或 a + (b - c)
        b = random.randint(5, 20)
        c = random.randint(5, 20)

        if random.random() < 0.5:
            # a - (b + c)
            a = random.randint(b + c + 5, b + c + 50)
            if not self.cache.add(8, a, b * 100 + c):
                return None
            return {
                "type": 8,
                "type_name": PROBLEM_TYPES[8]["name"],
                "question": f"{a} - ({b} + {c}) = ____",
                "answer": str(a - (b + c)),
                "work_lines": 2,
            }
        else:
            # a + (b - c) 或 a - (b - c)
            if b > c:
                a = random.randint(10, 50)
                if not self.cache.add(8, a, b * 100 + c):
                    return None
                if random.random() < 0.5:
                    return {
                        "type": 8,
                        "type_name": PROBLEM_TYPES[8]["name"],
                        "question": f"{a} + ({b} - {c}) = ____",
                        "answer": str(a + (b - c)),
                        "work_lines": 2,
                    }
                else:
                    a = random.randint(b - c + 10, b - c + 50)
                    return {
                        "type": 8,
                        "type_name": PROBLEM_TYPES[8]["name"],
                        "question": f"{a} - ({b} - {c}) = ____",
                        "answer": str(a - (b - c)),
                        "work_lines": 2,
                    }
            else:
                # b <= c, 退化为其他类型
                return self._generate_type7_mixed()

    def _generate_type9_fraction_decimal(self) -> Optional[Dict]:
        """类型9: 分数小数"""
        if self.grade < 4:
            # 低年级退化为类型4
            return self._generate_type4_multi_digit()

        if random.random() < 0.5:
            # 小数加法
            a = round(random.uniform(0.1, 5.0), 1)
            b = round(random.uniform(0.1, 5.0), 1)
            a_int = int(a * 10)
            b_int = int(b * 10)
            if not self.cache.add(9, a_int, b_int):
                return None
            return {
                "type": 9,
                "type_name": PROBLEM_TYPES[9]["name"],
                "question": f"{a} + {b} = ____",
                "answer": str(round(a + b, 1)),
                "work_lines": 1,
            }
        else:
            # 同分母分数
            denominator = random.choice([2, 3, 4, 5, 8, 10])
            a = random.randint(1, denominator - 1)
            b = random.randint(1, denominator - a)
            if not self.cache.add(9, denominator, a * 100 + b):
                return None
            return {
                "type": 9,
                "type_name": PROBLEM_TYPES[9]["name"],
                "question": f"{a}/{denominator} + {b}/{denominator} = ____",
                "answer": f"{a + b}/{denominator}",
                "work_lines": 1,
            }

    def _generate_type10_smart_calc(self) -> Optional[Dict]:
        """类型10: 巧算估算"""
        if random.random() < 0.3:
            # 25 × 4 = 100
            a = random.choice([25, 50, 75, 125])
            b = random.choice([4, 8])
            if not self.cache.add(10, a, b):
                return None
            return {
                "type": 10,
                "type_name": PROBLEM_TYPES[10]["name"],
                "question": f"{a} × {b} = ____",
                "answer": str(a * b),
                "work_lines": 1,
            }
        elif random.random() < 0.5:
            # 199 × 5 类型
            a = random.choice([99, 199, 299, 499])
            b = random.choice([2, 3, 4, 5])
            if not self.cache.add(10, a, b):
                return None
            return {
                "type": 10,
                "type_name": PROBLEM_TYPES[10]["name"],
                "question": f"{a} × {b} = ____",
                "answer": str(a * b),
                "work_lines": 1,
            }
        else:
            # 估算
            a = random.randint(300, 900)
            b = random.randint(300, 900)
            if not self.cache.add(10, a, b):
                return None
            rounded_a = round(a, -2)
            rounded_b = round(b, -2)
            return {
                "type": 10,
                "type_name": PROBLEM_TYPES[10]["name"],
                "question": f"估算: {a} + {b} ≈ ____",
                "answer": str(rounded_a + rounded_b),
                "work_lines": 1,
            }

    def generate_problem(self, problem_type: int) -> Dict:
        """生成单道指定类型的题目"""
        generators = {
            1: self._generate_type1_basic,
            2: self._generate_type2_carry_borrow,
            3: self._generate_type3_round_numbers,
            4: self._generate_type4_multi_digit,
            5: self._generate_type5_easy_calc,
            6: self._generate_type6_multiply_divide,
            7: self._generate_type7_mixed,
            8: self._generate_type8_parentheses,
            9: self._generate_type9_fraction_decimal,
            10: self._generate_type10_smart_calc,
        }

        generator = generators.get(problem_type, self._generate_type1_basic)
        return self._safe_generate(generator)

    def generate_quiz(self, count: int, types: List[int]) -> List[Dict]:
        """生成完整的小测"""
        self.cache.clear()
        problems = []

        # 均匀分配各题型
        type_counts = {}
        for i in range(count):
            type_idx = i % len(types)
            problem_type = types[type_idx]
            type_counts[problem_type] = type_counts.get(problem_type, 0) + 1

        # 生成各题型题目
        for problem_type, type_count in type_counts.items():
            for _ in range(type_count):
                problem = self.generate_problem(problem_type)
                problems.append(problem)

        # 打乱顺序并重新编号
        random.shuffle(problems)
        for i, problem in enumerate(problems, 1):
            problem["id"] = i

        return problems

    def get_summary(self, problems: List[Dict]) -> Dict:
        """统计题型分布"""
        summary = {}
        for p in problems:
            t = str(p["type"])
            summary[t] = summary.get(t, 0) + 1
        return summary
```

- [ ] **Step 4: 运行测试，确认通过**

```bash
pytest tests/test_math_generator.py -v
```

**Expected:** All tests pass

- [ ] **Step 5: 提交**

```bash
git add app/services/math_generator.py tests/test_math_generator.py
git commit -m "feat(generator): implement math problem generator with 10 types

- Add MathGenerator class with problem cache to avoid duplicates
- Implement all 10 problem type generators (basic, carry, round, etc.)
- Add grade-appropriate number ranges
- Comprehensive unit tests for generation logic

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: API 路由

### Task 3.1: 实现数学小测 API

**Files:**
- Create: `app/routers/math_quiz.py`
- Test: `tests/test_math_api.py`
- Modify: `app/main.py` (注册路由)

**Spec reference:** Section 5.1, 5.2

- [ ] **Step 1: 编写 API 测试**

```python
# tests/test_math_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestMathQuizAPI:
    def test_get_defaults_endpoint(self):
        """Test GET /api/math/quiz/defaults"""
        response = client.get("/api/math/quiz/defaults?grade=3")
        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "grade" in data
        assert data["grade"] == 3

    def test_get_defaults_invalid_grade(self):
        """Test defaults with invalid grade"""
        response = client.get("/api/math/quiz/defaults?grade=0")
        assert response.status_code == 422

    def test_generate_quiz_endpoint(self):
        """Test POST /api/math/quiz/generate"""
        response = client.post("/api/math/quiz/generate", json={
            "grade": 3,
            "count": 10,
            "types": [1, 2],
            "show_answers": False
        })
        assert response.status_code == 200
        data = response.json()
        assert "problems" in data
        assert len(data["problems"]) == 10
        assert "summary" in data
        assert data["grade"] == 3
        assert data["count"] == 10

    def test_generate_quiz_invalid_count(self):
        """Test generate with invalid count"""
        response = client.post("/api/math/quiz/generate", json={
            "grade": 3,
            "count": 5,  # Too low
            "types": [1]
        })
        assert response.status_code == 422

    def test_generate_quiz_missing_types(self):
        """Test generate without types"""
        response = client.post("/api/math/quiz/generate", json={
            "grade": 3,
            "count": 10
        })
        assert response.status_code == 422

    def test_problem_structure(self):
        """Verify problem has all required fields"""
        response = client.post("/api/math/quiz/generate", json={
            "grade": 2,
            "count": 5,
            "types": [1]
        })
        data = response.json()
        problem = data["problems"][0]
        assert "id" in problem
        assert "type" in problem
        assert "type_name" in problem
        assert "question" in problem
        assert "answer" in problem
        assert "work_lines" in problem

    def test_summary_accuracy(self):
        """Verify summary matches actual distribution"""
        response = client.post("/api/math/quiz/generate", json={
            "grade": 3,
            "count": 10,
            "types": [1, 2]
        })
        data = response.json()
        summary = data["summary"]
        total = sum(summary.values())
        assert total == 10
```

- [ ] **Step 2: 运行测试，确认失败**

```bash
pytest tests/test_math_api.py -v
```

**Expected:** FAIL - 404 errors (endpoints don't exist)

- [ ] **Step 3: 实现 API 路由**

```python
# app/routers/math_quiz.py
from fastapi import APIRouter, HTTPException, Query
from typing import List

from app.models.math_quiz import (
    MathQuizRequest,
    MathProblem,
    MathQuizResponse,
    GRADE_DEFAULTS,
    PROBLEM_TYPES,
)
from app.services.math_generator import MathGenerator

router = APIRouter(prefix="/api/math", tags=["math"])


@router.get("/quiz/defaults")
async def get_defaults(grade: int = Query(..., ge=1, le=6)):
    """获取年级默认题型"""
    return {
        "grade": grade,
        "types": GRADE_DEFAULTS.get(grade, GRADE_DEFAULTS[3]),
        "type_details": {
            str(t): PROBLEM_TYPES[t]
            for t in GRADE_DEFAULTS.get(grade, GRADE_DEFAULTS[3])
        },
    }


@router.post("/quiz/generate")
async def generate_quiz(request: MathQuizRequest):
    """生成数学小测题目"""
    generator = MathGenerator(request.grade)
    problems_data = generator.generate_quiz(request.count, request.types)

    problems = [MathProblem(**p) for p in problems_data]
    summary = generator.get_summary(problems_data)

    return MathQuizResponse(
        problems=problems,
        summary=summary,
        grade=request.grade,
        count=request.count,
    )
```

- [ ] **Step 4: 注册路由**

修改 `app/main.py`，添加路由导入和注册：

```python
# app/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import BASE_DIR
from app.routers import pages, api
from app.routers import math_quiz  # Add this import

app = FastAPI(
    title="语文学习小工具",
    description="帮助小学生每日校验汉字掌握情况",
    version="1.0.0"
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.mount("/data/pdfs", StaticFiles(directory=BASE_DIR / "data" / "pdfs"), name="pdfs")
app.include_router(pages.router)
app.include_router(api.router, prefix="/api")
app.include_router(math_quiz.router)  # Add this line

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

- [ ] **Step 5: 运行测试，确认通过**

```bash
pytest tests/test_math_api.py -v
```

**Expected:** All tests pass

- [ ] **Step 6: 提交**

```bash
git add app/routers/math_quiz.py tests/test_math_api.py app/main.py
git commit -m "feat(api): add math quiz API endpoints

- Add /api/math/quiz/defaults endpoint for grade defaults
- Add /api/math/quiz/generate endpoint for quiz generation
- Register routes in main.py
- Add comprehensive API tests

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: 页面路由和模板

### Task 4.1: 添加页面路由

**Files:**
- Modify: `app/routers/pages.py`

**Spec reference:** Section 3.1, 3.2, 3.3

- [ ] **Step 1: 在 pages.py 添加路由**

```python
# app/routers/pages.py - additions
from fastapi import APIRouter, Request, Query
from fastapi.templating import Jinja2Templates
from app.config import BASE_DIR
from app.models.math_quiz import PROBLEM_TYPES, GRADE_DEFAULTS

router = APIRouter()
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

# ... existing routes ...

@router.get("/math-quiz")
async def math_quiz_page(request: Request):
    """数学小测配置页面"""
    return templates.TemplateResponse("math_quiz.html", {
        "request": request,
        "problem_types": PROBLEM_TYPES,
        "grade_defaults": GRADE_DEFAULTS,
    })


@router.get("/math-quiz/preview")
async def math_preview_page(
    request: Request,
    grade: int = Query(..., ge=1, le=6),
    count: int = Query(15, ge=10, le=20),
    types: str = Query(...),
    show_answers: bool = Query(False),
):
    """数学小测预览/打印页面"""
    from app.services.math_generator import MathGenerator

    type_list = [int(t) for t in types.split(",") if t]
    generator = MathGenerator(grade)
    problems = generator.generate_quiz(count, type_list)

    return templates.TemplateResponse("math_preview.html", {
        "request": request,
        "grade": grade,
        "count": count,
        "problems": problems,
        "show_answers": show_answers,
        "today": __import__("datetime").datetime.now().strftime("%Y年%m月%d日"),
    })
```

- [ ] **Step 2: 提交**

```bash
git add app/routers/pages.py
git commit -m "feat(pages): add math quiz page routes

- Add /math-quiz config page route
- Add /math-quiz/preview page route with query params

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Task 4.2: 首页添加入口

**Files:**
- Modify: `app/templates/index.html`

- [ ] **Step 1: 在 Quick Links 添加第四个卡片**

在 `index.html` 中找到 Quick Links 区域（约第 47 行），在第三个卡片后添加：

```html
<!-- Add this after the PDFs card (around line 68) -->
<a href="/math-quiz" class="bg-white rounded-xl shadow p-6 hover:shadow-lg transition flex items-center space-x-4">
    <span class="text-4xl">📐</span>
    <div>
        <h3 class="font-bold text-gray-800">数学每日小测</h3>
        <p class="text-sm text-gray-500">生成可打印的数学练习题</p>
    </div>
</a>
```

- [ ] **Step 2: 提交**

```bash
git add app/templates/index.html
git commit -m "feat(ui): add math quiz entry card to homepage

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 5: 前端模板

### Task 5.1: 配置页面模板

**Files:**
- Create: `app/templates/math_quiz.html`

**Spec reference:** Section 3.2

- [ ] **Step 1: 创建配置页面**

```html
<!-- app/templates/math_quiz.html -->
{% extends "base.html" %}

{% block title %}数学每日小测 - 配置{% endblock %}

{% block content %}
<div class="max-w-3xl mx-auto">
    <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-gray-800 mb-2">📐 数学每日小测</h1>
        <p class="text-gray-600">选择年级和题型，生成专属练习题</p>
    </div>

    <div class="bg-white rounded-2xl shadow-lg p-6 mb-6">
        <!-- Grade Selection -->
        <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-3">选择年级</label>
            <div class="flex flex-wrap gap-2" id="grade-selector">
                {% for g in range(1, 7) %}
                <button type="button" data-grade="{{ g }}"
                    class="grade-btn px-4 py-2 rounded-lg border-2 font-medium transition
                           {% if g == 3 %}border-blue-500 bg-blue-50 text-blue-700{% else %}border-gray-200 text-gray-600 hover:border-gray-300{% endif %}">
                    {{ g }}年级
                </button>
                {% endfor %}
            </div>
        </div>

        <!-- Count Selection -->
        <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-2">
                题目数量: <span id="count-display" class="text-blue-600 font-bold">15</span> 道
            </label>
            <input type="range" id="count" min="10" max="20" value="15"
                   class="w-full h-3 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-500">
            <div class="flex justify-between text-xs text-gray-500 mt-1">
                <span>10</span>
                <span>20</span>
            </div>
        </div>

        <!-- Problem Types -->
        <div class="mb-6">
            <label class="block text-sm font-medium text-gray-700 mb-3">选择题型</label>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3" id="type-selector">
                {% for type_id, type_info in problem_types.items() %}
                <label class="flex items-start space-x-2 p-3 border-2 rounded-lg cursor-pointer hover:bg-gray-50 transition type-option"
                       data-type="{{ type_id }}">
                    <input type="checkbox" value="{{ type_id }}" class="type-checkbox w-5 h-5 text-blue-500 rounded focus:ring-blue-500 mt-0.5">
                    <div class="flex-1">
                        <div class="font-medium text-sm">{{ type_info.name }}</div>
                        <div class="text-xs text-gray-500">{{ type_info.desc }}</div>
                    </div>
                </label>
                {% endfor %}
            </div>
        </div>

        <!-- Show Answers -->
        <div class="mb-6">
            <label class="flex items-center space-x-2 cursor-pointer">
                <input type="checkbox" id="show-answers" class="w-5 h-5 text-blue-500 rounded focus:ring-blue-500">
                <span class="text-gray-700">显示答案（答案将显示在页面底部）</span>
            </label>
        </div>

        <!-- Generate Button -->
        <button id="generate-btn" disabled
                class="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-bold py-4 px-8 rounded-xl text-xl shadow-lg transform transition hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none">
            🚀 生成小测
        </button>
    </div>
</div>

<script>
// Grade defaults configuration
const gradeDefaults = {{ grade_defaults | tojson }};
let currentGrade = 3;

// Update type checkboxes based on grade
function updateTypeSelection(grade) {
    const defaults = gradeDefaults[grade] || gradeDefaults[3];
    document.querySelectorAll('.type-checkbox').forEach(cb => {
        cb.checked = defaults.includes(parseInt(cb.value));
    });
    updateGenerateButton();
}

// Grade button click handlers
document.querySelectorAll('.grade-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update visual selection
        document.querySelectorAll('.grade-btn').forEach(b => {
            b.classList.remove('border-blue-500', 'bg-blue-50', 'text-blue-700');
            b.classList.add('border-gray-200', 'text-gray-600');
        });
        btn.classList.remove('border-gray-200', 'text-gray-600');
        btn.classList.add('border-blue-500', 'bg-blue-50', 'text-blue-700');

        // Update types
        currentGrade = parseInt(btn.dataset.grade);
        updateTypeSelection(currentGrade);
    });
});

// Count slider
document.getElementById('count').addEventListener('input', (e) => {
    document.getElementById('count-display').textContent = e.target.value;
});

// Type checkbox change handlers
document.querySelectorAll('.type-checkbox').forEach(cb => {
    cb.addEventListener('change', updateGenerateButton);
});

// Update generate button state
function updateGenerateButton() {
    const checked = document.querySelectorAll('.type-checkbox:checked');
    document.getElementById('generate-btn').disabled = checked.length === 0;
}

// Generate button click
document.getElementById('generate-btn').addEventListener('click', () => {
    const grade = currentGrade;
    const count = document.getElementById('count').value;
    const types = Array.from(document.querySelectorAll('.type-checkbox:checked'))
        .map(cb => cb.value)
        .join(',');
    const showAnswers = document.getElementById('show-answers').checked ? '1' : '0';

    window.location.href = `/math-quiz/preview?grade=${grade}&count=${count}&types=${types}&show_answers=${showAnswers}`;
});

// Initialize
updateTypeSelection(3);
</script>
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add app/templates/math_quiz.html
git commit -m "feat(ui): add math quiz config page template

- Grade selector with 1-6 buttons
- Count slider (10-20)
- 10 problem type checkboxes with grade defaults
- Show answers checkbox
- Generate button with validation

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Task 5.2: 预览页面模板

**Files:**
- Create: `app/templates/math_preview.html`

**Spec reference:** Section 3.3

- [ ] **Step 1: 创建预览页面**

```html
<!-- app/templates/math_preview.html -->
{% extends "base.html" %}

{% block title %}数学每日小测 - 预览{% endblock %}

{% block content %}
<!-- Print Controls (hidden when printing) -->
<div class="no-print max-w-4xl mx-auto mb-6 flex justify-between items-center">
    <a href="/math-quiz" class="text-blue-600 hover:text-blue-800 flex items-center space-x-1">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/>
        </svg>
        <span>返回修改</span>
    </a>
    <button onclick="window.print()" class="bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-lg flex items-center space-x-2">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z"/>
        </svg>
        <span>打印</span>
    </button>
</div>

<!-- Printable Content -->
<div class="print-content max-w-4xl mx-auto bg-white p-8 shadow-lg">
    <!-- Header -->
    <div class="text-center mb-8 pb-4 border-b-2 border-gray-800">
        <h1 class="text-2xl font-bold text-gray-900">数学每日小测</h1>
        <div class="mt-2 text-gray-600">
            <span class="mr-4">{{ grade }}年级</span>
            <span>{{ today }}</span>
        </div>
    </div>

    <!-- Problems Grid -->
    <div class="grid grid-cols-2 gap-x-12 gap-y-6">
        {% for problem in problems %}
        <div class="problem-item">
            <div class="flex items-start">
                <span class="font-bold text-gray-700 mr-2 w-8">{{ problem.id }}.</span>
                <div class="flex-1">
                    <div class="text-lg font-medium text-gray-900">{{ problem.question }}</div>
                    {% if problem.work_lines > 1 %}
                    <div class="mt-2 space-y-1">
                        {% for i in range(problem.work_lines) %}
                        <div class="border-b border-gray-300 h-6"></div>
                        {% endfor %}
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>

    <!-- Answers Section -->
    {% if show_answers %}
    <div class="mt-12 pt-6 border-t-2 border-gray-300">
        <h3 class="text-lg font-bold text-gray-800 mb-4">参考答案</h3>
        <div class="grid grid-cols-5 gap-3">
            {% for problem in problems %}
            <div class="text-center py-2 bg-gray-50 rounded">
                <span class="text-gray-500 text-sm">{{ problem.id }}.</span>
                <span class="font-medium text-gray-900 ml-1">{{ problem.answer }}</span>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <!-- Footer -->
    <div class="mt-12 pt-4 border-t border-gray-300 text-center text-sm text-gray-500">
        <p>姓名：_______________  得分：_______________</p>
    </div>
</div>

<style>
/* Print styles */
@media print {
    .no-print {
        display: none !important;
    }

    body {
        background: white;
    }

    .print-content {
        box-shadow: none;
        padding: 0;
        max-width: 100%;
    }

    /* Page settings */
    @page {
        size: A4;
        margin: 15mm;
    }

    /* Ensure problems don't break across pages */
    .problem-item {
        break-inside: avoid;
    }

    /* Hide answers section on first page if needed */
    {% if show_answers %}
    .print-content > div:last-of-type {
        break-before: page;
    }
    {% endif %}
}

/* Screen styles */
@media screen {
    .print-content {
        min-height: 600px;
    }
}
</style>
{% endblock %}
```

- [ ] **Step 2: 提交**

```bash
git add app/templates/math_preview.html
git commit -m "feat(ui): add math quiz preview/print page template

- Two-column problem layout
- Print-optimized styling with @media print
- Optional answers section at bottom
- Name/score footer field
- Back and Print buttons

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 6: 集成测试和验证

### Task 6.1: 运行完整测试套件

- [ ] **Step 1: 运行所有测试**

```bash
cd /Users/liuwenping/Documents/fliggy/study-class
pytest tests/ -v --tb=short
```

**Expected:** All tests pass

- [ ] **Step 2: 手动验证页面**

启动服务并验证：

```bash
python -m uvicorn app.main:app --reload
```

访问验证：
1. `http://localhost:8000/` - 确认首页有"数学每日小测"卡片
2. `http://localhost:8000/math-quiz` - 确认配置页面正常
3. 选择年级 3，点击生成 - 确认跳转到预览页
4. `http://localhost:8000/math-quiz/preview?grade=3&count=10&types=1,2&show_answers=1` - 确认题目和答案显示

- [ ] **Step 3: 提交最终变更**

```bash
git add .
git commit -m "feat(math-quiz): complete math daily quiz feature implementation

- Add 10 problem types with grade-appropriate difficulty
- Implement problem generator with uniqueness cache
- Add API endpoints for defaults and quiz generation
- Create config and preview page templates
- Add print-optimized CSS styles
- Full test coverage for models, generator, and API

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Summary

| Component | Files | Status |
|-----------|-------|--------|
| Data Models | `app/models/math_quiz.py` | ✅ TDD |
| Problem Generator | `app/services/math_generator.py` | ✅ TDD |
| API Routes | `app/routers/math_quiz.py` | ✅ TDD |
| Page Routes | `app/routers/pages.py` | ✅ |
| Config Page | `app/templates/math_quiz.html` | ✅ |
| Preview Page | `app/templates/math_preview.html` | ✅ |
| Homepage Entry | `app/templates/index.html` | ✅ |
| Tests | `tests/test_math_*.py` | ✅ TDD |

**Total estimated time:** 2-3 hours
**Commits:** 6-7 atomic commits
