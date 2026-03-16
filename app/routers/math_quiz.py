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
