import random
from typing import Dict, List, Set, Tuple, Optional
from fractions import Fraction

from app.models.math_quiz import PROBLEM_TYPES, GRADE_RANGES


class ProblemCache:
    """避免生成重复题目"""

    def __init__(self):
        self._cache: Set[Tuple[int, int, int]] = set()

    def add(self, problem_type: int, a: int, b: int) -> bool:
        """添加题目到缓存，返回是否成功（False表示重复）"""
        key = (problem_type, a, b)
        if key in self._cache:
            return False
        self._cache.add(key)
        return True

    def clear(self):
        """清空缓存"""
        self._cache.clear()


class MathGenerator:
    """数学题目生成器"""

    def __init__(self, grade: int):
        self.grade = grade
        self.ranges = GRADE_RANGES.get(grade, GRADE_RANGES[3])
        self.cache = ProblemCache()

    def generate_problem(self, problem_type: int) -> Dict:
        """生成指定类型的单道题目"""
        generator_map = {
            1: self._generate_type1,
            2: self._generate_type2,
            3: self._generate_type3,
            4: self._generate_type4,
            5: self._generate_type5,
            6: self._generate_type6,
            7: self._generate_type7,
            8: self._generate_type8,
            9: self._generate_type9,
            10: self._generate_type10,
        }

        if problem_type not in generator_map:
            raise ValueError(f"Unknown problem type: {problem_type}")

        return generator_map[problem_type]()

    def generate_quiz(self, count: int, types: List[int]) -> List[Dict]:
        """生成完整的小测题目"""
        if not types:
            raise ValueError("Types list cannot be empty")

        # 验证题型值
        for t in types:
            if t < 1 or t > 10:
                raise ValueError(f"Invalid problem type: {t}. Must be 1-10")

        # 清空缓存
        self.cache.clear()

        problems = []
        max_attempts = count * 100  # 防止无限循环
        attempts = 0

        # 均匀分配各题型数量
        type_counts = self._distribute_types(count, types)

        for problem_type, num in type_counts.items():
            generated = 0
            while generated < num and attempts < max_attempts:
                attempts += 1
                problem = self.generate_problem(problem_type)
                # 提取关键数字用于去重检查
                key_nums = self._extract_key_numbers(problem["question"], problem_type)
                if key_nums and self.cache.add(problem_type, key_nums[0], key_nums[1]):
                    problems.append(problem)
                    generated += 1

        # 打乱顺序
        random.shuffle(problems)

        # 重新编号
        for i, p in enumerate(problems, 1):
            p["id"] = i

        return problems

    def _distribute_types(self, count: int, types: List[int]) -> Dict[int, int]:
        """均匀分配各题型数量"""
        type_counts = {}
        base = count // len(types)
        remainder = count % len(types)

        for i, t in enumerate(types):
            type_counts[t] = base + (1 if i < remainder else 0)

        return type_counts

    def _extract_key_numbers(self, question: str, problem_type: int) -> Optional[Tuple[int, int]]:
        """从题目中提取关键数字用于去重"""
        try:
            q = question.replace(" = ____", "").replace(" ", "")

            if problem_type == 9:  # 分数小数
                if "/" in q:
                    parts = q.replace("=", "").split("+")
                    if len(parts) == 2:
                        a = int(parts[0].split("/")[0])
                        b = int(parts[1].split("/")[0])
                        return (a, b)
                elif "." in q:
                    parts = q.split("+")
                    if len(parts) == 2:
                        a = int(float(parts[0]) * 10)
                        b = int(float(parts[1]) * 10)
                        return (a, b)

            if "+" in q:
                a, b = map(int, q.split("+")[:2])
                return (a, b)
            elif "-" in q:
                parts = q.split("-")
                if len(parts) == 2:
                    a, b = map(int, parts)
                    return (a, b)
            elif "×" in q:
                a, b = map(int, q.split("×")[:2])
                return (a, b)
            elif "÷" in q:
                parts = q.split("÷")
                if len(parts) == 2:
                    a, b = map(int, parts)
                    return (a, b)
        except (ValueError, IndexError):
            pass

        # 对于复杂表达式，使用哈希
        return (hash(question) % 10000, 0)

    def get_summary(self, problems: List[Dict]) -> Dict:
        """统计题型分布"""
        by_type = {}
        for p in problems:
            t = p["type"]
            by_type[t] = by_type.get(t, 0) + 1

        return {
            "total": len(problems),
            "by_type": by_type,
        }

    # ========== 题型生成器 ==========

    def _generate_type1(self) -> Dict:
        """类型1: 基本加减（不进位/不退位）"""
        min_val, max_val = self.ranges["add_sub"]

        if random.choice([True, False]):  # 加法
            # 确保不进位
            max_digit = min(9, max_val // 10)
            a_tens = random.randint(0, max_digit)
            b_tens = random.randint(0, max_digit)
            a_ones = random.randint(0, 4)  # 确保个位相加 < 10
            b_ones = random.randint(0, 4)

            a = a_tens * 10 + a_ones
            b = b_tens * 10 + b_ones

            # 确保在范围内
            while a > max_val or b > max_val or a + b > max_val:
                a_tens = random.randint(0, max_digit)
                b_tens = random.randint(0, max_digit)
                a_ones = random.randint(0, 4)
                b_ones = random.randint(0, 4)
                a = a_tens * 10 + a_ones
                b = b_tens * 10 + b_ones

            question = f"{a} + {b} = ____"
            answer = str(a + b)
        else:  # 减法
            a = random.randint(10, max_val)
            # 确保不退位
            a_ones = a % 10
            b_ones = random.randint(0, a_ones)
            b_tens = random.randint(0, a // 10)
            b = b_tens * 10 + b_ones

            while b > a:
                b_tens = random.randint(0, a // 10 - 1)
                b = b_tens * 10 + b_ones

            question = f"{a} - {b} = ____"
            answer = str(a - b)

        return {
            "id": 0,
            "type": 1,
            "type_name": PROBLEM_TYPES[1]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }

    def _generate_type2(self) -> Dict:
        """类型2: 进位退位"""
        min_val, max_val = self.ranges["add_sub"]

        if random.choice([True, False]):  # 进位加法
            a = random.randint(10, max_val // 2)
            b = random.randint(10, max_val // 2)

            # 确保进位
            a_ones = a % 10
            b_ones = b % 10
            if a_ones + b_ones < 10:
                b = b + (10 - a_ones)

            question = f"{a} + {b} = ____"
            answer = str(a + b)
        else:  # 退位减法
            a = random.randint(20, max_val)
            b = random.randint(10, a - 1)

            # 确保退位
            a_ones = a % 10
            b_ones = b % 10
            if a_ones >= b_ones:
                b = (b // 10) * 10 + (a_ones + 1)
                if b >= a:
                    b = b - 10

            question = f"{a} - {b} = ____"
            answer = str(a - b)

        return {
            "id": 0,
            "type": 2,
            "type_name": PROBLEM_TYPES[2]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }

    def _generate_type3(self) -> Dict:
        """类型3: 整十整百"""
        min_val, max_val = self.ranges["add_sub"]

        if max_val >= 1000:
            # 使用整百
            base = 100
            max_unit = max_val // 100
        else:
            # 使用整十
            base = 10
            max_unit = max_val // 10

        a = random.randint(1, max_unit) * base
        b = random.randint(1, max_unit) * base

        if random.choice([True, False]):  # 加法
            while a + b > max_val:
                a = random.randint(1, max_unit) * base
                b = random.randint(1, max_unit) * base
            question = f"{a} + {b} = ____"
            answer = str(a + b)
        else:  # 减法
            if b > a:
                a, b = b, a
            question = f"{a} - {b} = ____"
            answer = str(a - b)

        return {
            "id": 0,
            "type": 3,
            "type_name": PROBLEM_TYPES[3]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }

    def _generate_type4(self) -> Dict:
        """类型4: 多位数加减"""
        min_val, max_val = self.ranges["add_sub"]

        # 根据年级确定位数
        if max_val >= 10000:
            digits = random.choice([2, 3, 3])  # 主要出三位数
        else:
            digits = 2

        max_num = min(10 ** digits - 1, max_val)
        min_num = 10 ** (digits - 1)

        a = random.randint(min_num, max_num)
        b = random.randint(min_num, max_num)

        if random.choice([True, False]):  # 加法
            while a + b > max_val:
                a = random.randint(min_num, max_num)
                b = random.randint(min_num, max_num)
            question = f"{a} + {b} = ____"
            answer = str(a + b)
        else:  # 减法
            if b > a:
                a, b = b, a
            question = f"{a} - {b} = ____"
            answer = str(a - b)

        return {
            "id": 0,
            "type": 4,
            "type_name": PROBLEM_TYPES[4]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }

    def _generate_type5(self) -> Dict:
        """类型5: 简便计算（凑整法）"""
        patterns = [
            # 99 + x
            lambda: (99, random.randint(1, 100)),
            # 98 + x
            lambda: (98, random.randint(2, 100)),
            # 101 - x
            lambda: (101, random.randint(1, 100)),
            # x + 25 (凑100)
            lambda: (random.randint(1, 100), 75),
            # 198 + x
            lambda: (198, random.randint(2, 100)),
        ]

        pattern = random.choice(patterns)
        a, b = pattern()

        # 确保在范围内
        min_val, max_val = self.ranges["add_sub"]
        max_num = min(999, max_val // 2)
        a = min(a, max_num)
        b = min(b, max_num)

        if random.choice([True, False]):
            question = f"{a} + {b} = ____"
            answer = str(a + b)
        else:
            if b > a:
                a, b = b, a
            question = f"{a} - {b} = ____"
            answer = str(a - b)

        return {
            "id": 0,
            "type": 5,
            "type_name": PROBLEM_TYPES[5]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }

    def _generate_type6(self) -> Dict:
        """类型6: 乘除口诀"""
        mul_range = self.ranges.get("mul_div", (1, 9))
        max_table = min(mul_range[1], 9)  # 限制在九九乘法表

        if random.choice([True, False]):  # 乘法
            a = random.randint(1, max_table)
            b = random.randint(1, max_table)
            question = f"{a} × {b} = ____"
            answer = str(a * b)
        else:  # 除法
            b = random.randint(1, max_table)
            result = random.randint(1, max_table)
            a = b * result
            question = f"{a} ÷ {b} = ____"
            answer = str(result)

        return {
            "id": 0,
            "type": 6,
            "type_name": PROBLEM_TYPES[6]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }

    def _generate_type7(self) -> Dict:
        """类型7: 多步混合"""
        mul_range = self.ranges.get("mul_div", (1, 9))
        max_table = min(mul_range[1], 9)

        patterns = [
            # a + b - c
            lambda: (random.randint(10, 100), random.randint(10, 50), random.randint(1, 30)),
            # a - b + c
            lambda: (random.randint(50, 100), random.randint(10, 40), random.randint(10, 40)),
            # a × b + c
            lambda: (random.randint(2, max_table), random.randint(2, max_table), random.randint(1, 50)),
            # a + b × c
            lambda: (random.randint(10, 50), random.randint(2, max_table), random.randint(2, 5)),
            # a × b - c
            lambda: (random.randint(2, max_table), random.randint(2, max_table), random.randint(1, 20)),
            # a ÷ b + c
            lambda: self._make_division_add(max_table),
        ]

        pattern = random.choice(patterns)
        a, b, c = pattern()

        # 根据模式生成题目
        r = random.randint(0, 5)
        if r == 0:
            question = f"{a} + {b} - {c} = ____"
            answer = str(a + b - c)
        elif r == 1:
            question = f"{a} - {b} + {c} = ____"
            answer = str(a - b + c)
        elif r == 2:
            question = f"{a} × {b} + {c} = ____"
            answer = str(a * b + c)
        elif r == 3:
            question = f"{a} + {b} × {c} = ____"
            answer = str(a + b * c)
        elif r == 4:
            question = f"{a} × {b} - {c} = ____"
            answer = str(a * b - c)
        else:
            question = f"{a} ÷ {b} + {c} = ____"
            answer = str(a // b + c)

        return {
            "id": 0,
            "type": 7,
            "type_name": PROBLEM_TYPES[7]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 2,
        }

    def _make_division_add(self, max_table: int) -> Tuple[int, int, int]:
        """生成除法加法的数字"""
        b = random.randint(2, max_table)
        result = random.randint(2, max_table)
        a = b * result
        c = random.randint(1, 50)
        return (a, b, c)

    def _generate_type8(self) -> Dict:
        """类型8: 括号运算"""
        mul_range = self.ranges.get("mul_div", (1, 9))
        max_table = min(mul_range[1], 9)

        patterns = [
            # a + (b + c)
            lambda: (random.randint(10, 100), random.randint(1, 50), random.randint(1, 50)),
            # a - (b + c)
            lambda: (random.randint(50, 150), random.randint(10, 40), random.randint(10, 40)),
            # a × (b + c)
            lambda: (random.randint(2, 9), random.randint(2, 10), random.randint(2, 10)),
            # (a + b) × c
            lambda: (random.randint(5, 20), random.randint(5, 20), random.randint(2, 9)),
            # a + (b - c)
            lambda: (random.randint(10, 50), random.randint(20, 60), random.randint(1, 15)),
        ]

        pattern = random.choice(patterns)
        a, b, c = pattern()

        r = random.randint(0, 4)
        if r == 0:
            question = f"{a} + ({b} + {c}) = ____"
            answer = str(a + b + c)
        elif r == 1:
            question = f"{a} - ({b} + {c}) = ____"
            answer = str(a - (b + c))
        elif r == 2:
            question = f"{a} × ({b} + {c}) = ____"
            answer = str(a * (b + c))
        elif r == 3:
            question = f"({a} + {b}) × {c} = ____"
            answer = str((a + b) * c)
        else:
            question = f"{a} + ({b} - {c}) = ____"
            answer = str(a + (b - c))

        return {
            "id": 0,
            "type": 8,
            "type_name": PROBLEM_TYPES[8]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 2,
        }

    def _generate_type9(self) -> Dict:
        """类型9: 分数小数"""
        has_decimal = self.ranges.get("decimal", False)
        has_fraction = self.ranges.get("fraction", False)

        if has_fraction and random.choice([True, False]):
            # 同分母分数
            denominator = random.choice([2, 3, 4, 5, 6, 8, 10])
            a = random.randint(1, denominator - 1)
            b = random.randint(1, denominator - 1)

            if random.choice([True, False]):  # 加法
                question = f"{a}/{denominator} + {b}/{denominator} = ____"
                result = Fraction(a, denominator) + Fraction(b, denominator)
                answer = f"{result.numerator}/{result.denominator}" if result.denominator != 1 else str(result.numerator)
            else:  # 减法
                if b > a:
                    a, b = b, a
                question = f"{a}/{denominator} - {b}/{denominator} = ____"
                result = Fraction(a, denominator) - Fraction(b, denominator)
                answer = f"{result.numerator}/{result.denominator}" if result.denominator != 1 else str(result.numerator)
        elif has_decimal:
            # 简单小数
            a = round(random.uniform(0.1, 5.0), 1)
            b = round(random.uniform(0.1, 5.0), 1)

            if random.choice([True, False]):  # 加法
                question = f"{a} + {b} = ____"
                answer = str(round(a + b, 1))
            else:  # 减法
                if b > a:
                    a, b = b, a
                question = f"{a} - {b} = ____"
                answer = str(round(a - b, 1))
        else:
            # 降级为整数
            a = random.randint(1, 20)
            b = random.randint(1, 20)
            if random.choice([True, False]):
                question = f"{a} + {b} = ____"
                answer = str(a + b)
            else:
                if b > a:
                    a, b = b, a
                question = f"{a} - {b} = ____"
                answer = str(a - b)

        return {
            "id": 0,
            "type": 9,
            "type_name": PROBLEM_TYPES[9]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }

    def _generate_type10(self) -> Dict:
        """类型10: 巧算估算"""
        patterns = [
            # 25 × 4
            (25, 4),
            (25, 8),
            (125, 8),
            (125, 4),
            # 199 × n
            (199, random.randint(2, 5)),
            (299, random.randint(2, 5)),
            # 101 × n
            (101, random.randint(2, 9)),
            (1001, random.randint(2, 5)),
        ]

        a, b = random.choice(patterns)

        if isinstance(b, int):
            question = f"{a} × {b} = ____"
            answer = str(a * b)
        else:
            question = f"{a} × {b} = ____"
            answer = str(a * b)

        return {
            "id": 0,
            "type": 10,
            "type_name": PROBLEM_TYPES[10]["name"],
            "question": question,
            "answer": answer,
            "work_lines": 1,
        }
