import pytest
from pydantic import ValidationError
from app.models.math_quiz import MathQuizRequest, MathProblem, PROBLEM_TYPES


def test_math_quiz_request_valid():
    """Test valid request creation"""
    req = MathQuizRequest(grade=3, count=30, types=[1, 2, 3], show_answers=True)
    assert req.grade == 3
    assert req.count == 30
    assert req.types == [1, 2, 3]
    assert req.show_answers is True


def test_math_quiz_request_defaults():
    """Test default values"""
    req = MathQuizRequest(grade=2, types=[1])
    assert req.count == 30
    assert req.show_answers is False


def test_math_quiz_request_grade_bounds():
    """Test grade must be 1-6"""
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=0, types=[1])
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=7, types=[1])


def test_math_quiz_request_count_bounds():
    """Test count must be 10-30"""
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=3, count=5, types=[1])
    with pytest.raises(ValidationError):
        MathQuizRequest(grade=3, count=35, types=[1])


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
