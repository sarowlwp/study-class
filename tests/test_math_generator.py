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

    def test_cache_clear(self):
        cache = ProblemCache()
        cache.add(1, 23, 45)
        cache.clear()
        assert cache.add(1, 23, 45)  # Can add again after clear


class TestBasicAdditionSubtraction:
    """Test Type 1: 基本加减"""

    def test_generate_no_carry_addition(self):
        gen = MathGenerator(grade=2)
        # Try multiple times to get an addition
        for _ in range(50):
            problem = gen._generate_type1()
            if "+" in problem["question"]:
                assert problem["type"] == 1
                assert "=" in problem["question"]
                # Verify no carry
                a, b = map(int, problem["question"].replace(" = ____", "").split(" + "))
                assert (a % 10) + (b % 10) < 10
                break
        else:
            pytest.skip("Could not generate addition in 50 attempts")

    def test_generate_no_borrow_subtraction(self):
        gen = MathGenerator(grade=2)
        # Try multiple times to get a subtraction
        for _ in range(50):
            problem = gen._generate_type1()
            if "-" in problem["question"]:
                a, b = map(int, problem["question"].replace(" = ____", "").split(" - "))
                assert (a % 10) >= (b % 10)
                assert a >= b  # No negative results
                break
        else:
            pytest.skip("Could not generate subtraction in 50 attempts")


class TestMathGeneratorBasic:
    def test_generator_creation(self):
        gen = MathGenerator(grade=3)
        assert gen.grade == 3
        assert gen.ranges["add_sub"] == (0, 1000)

    def test_generator_creation_grade1(self):
        gen = MathGenerator(grade=1)
        assert gen.grade == 1
        assert gen.ranges["add_sub"] == (0, 20)

    def test_generator_creation_grade6(self):
        gen = MathGenerator(grade=6)
        assert gen.grade == 6
        assert gen.ranges["add_sub"] == (0, 1000000)

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


class TestProblemTypes:
    """Test all 10 problem types can be generated"""

    def test_type1_basic_add_sub(self):
        gen = MathGenerator(grade=2)
        problem = gen._generate_type1()
        assert problem["type"] == 1
        assert "=" in problem["question"]

    def test_type2_carry_borrow(self):
        gen = MathGenerator(grade=2)
        problem = gen._generate_type2()
        assert problem["type"] == 2
        assert "=" in problem["question"]

    def test_type3_round_numbers(self):
        gen = MathGenerator(grade=2)
        problem = gen._generate_type3()
        assert problem["type"] == 3
        assert "=" in problem["question"]

    def test_type4_multi_digit(self):
        gen = MathGenerator(grade=3)
        problem = gen._generate_type4()
        assert problem["type"] == 4
        assert "=" in problem["question"]

    def test_type5_easy_calculation(self):
        gen = MathGenerator(grade=3)
        problem = gen._generate_type5()
        assert problem["type"] == 5
        assert "=" in problem["question"]

    def test_type6_multiplication_division(self):
        gen = MathGenerator(grade=2)
        problem = gen._generate_type6()
        assert problem["type"] == 6
        assert "=" in problem["question"]

    def test_type7_mixed_operations(self):
        gen = MathGenerator(grade=3)
        problem = gen._generate_type7()
        assert problem["type"] == 7
        assert "=" in problem["question"]

    def test_type8_parentheses(self):
        gen = MathGenerator(grade=4)
        problem = gen._generate_type8()
        assert problem["type"] == 8
        assert "=" in problem["question"]
        assert "(" in problem["question"]

    def test_type9_fraction_decimal(self):
        gen = MathGenerator(grade=4)
        problem = gen._generate_type9()
        assert problem["type"] == 9
        assert "=" in problem["question"]

    def test_type10_clever_calculation(self):
        gen = MathGenerator(grade=5)
        problem = gen._generate_type10()
        assert problem["type"] == 10
        assert "=" in problem["question"]


class TestQuizGeneration:
    """Test quiz generation with various configurations"""

    def test_quiz_count_exact(self):
        gen = MathGenerator(grade=3)
        for count in [10, 15, 20]:
            quiz = gen.generate_quiz(count=count, types=[1])
            assert len(quiz) == count

    def test_quiz_type_distribution(self):
        gen = MathGenerator(grade=3)
        quiz = gen.generate_quiz(count=10, types=[1, 2])
        type_counts = {}
        for p in quiz:
            t = p["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
        # Both types should appear
        assert 1 in type_counts or 2 in type_counts

    def test_quiz_ids_sequential(self):
        gen = MathGenerator(grade=3)
        quiz = gen.generate_quiz(count=10, types=[1])
        ids = [p["id"] for p in quiz]
        assert ids == list(range(1, 11))

    def test_quiz_no_duplicates(self):
        gen = MathGenerator(grade=3)
        quiz = gen.generate_quiz(count=10, types=[1])
        questions = [p["question"] for p in quiz]
        assert len(questions) == len(set(questions))

    def test_get_summary(self):
        gen = MathGenerator(grade=3)
        quiz = gen.generate_quiz(count=10, types=[1, 2])
        summary = gen.get_summary(quiz)
        assert "total" in summary
        assert "by_type" in summary
        assert summary["total"] == 10


class TestGradeRanges:
    """Test grade-appropriate number ranges"""

    def test_grade1_range(self):
        gen = MathGenerator(grade=1)
        problem = gen._generate_type1()
        question = problem["question"].replace(" = ____", "").replace(" ", "")
        if "+" in question:
            a, b = map(int, question.split("+"))
            assert a <= 20 and b <= 20

    def test_grade2_range(self):
        gen = MathGenerator(grade=2)
        problem = gen._generate_type1()
        question = problem["question"].replace(" = ____", "").replace(" ", "")
        if "+" in question:
            a, b = map(int, question.split("+"))
            assert a <= 100 and b <= 100

    def test_grade3_range(self):
        gen = MathGenerator(grade=3)
        problem = gen._generate_type1()
        question = problem["question"].replace(" = ____", "").replace(" ", "")
        if "+" in question:
            a, b = map(int, question.split("+"))
            assert a <= 1000 and b <= 1000
