from pydantic import BaseModel, Field
from typing import List


class MathQuizRequest(BaseModel):
    """生成数学小测请求"""
    grade: int = Field(..., ge=1, le=6, description="年级 1-6")
    count: int = Field(30, ge=10, le=30, description="题目数量 10-30")
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
    1: [1, 2, 5],
    2: [1, 2, 3, 5, 6],
    3: [1, 2, 3, 4, 5, 6, 7],
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
