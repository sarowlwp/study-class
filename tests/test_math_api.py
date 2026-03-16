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
            "count": 10,
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
        assert summary["total"] == 10
        by_type_total = sum(summary["by_type"].values())
        assert by_type_total == 10
