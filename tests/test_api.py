from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_semesters():
    response = client.get("/api/semesters")
    assert response.status_code == 200
    data = response.json()
    assert "semesters" in data
    assert len(data["semesters"]) >= 1


def test_get_lessons():
    response = client.get("/api/lessons?semester=grade1-spring")
    assert response.status_code == 200
    data = response.json()
    assert "lessons" in data
    assert len(data["lessons"]) == 2


def test_get_characters():
    response = client.get("/api/characters?semester=grade1-spring")
    assert response.status_code == 200
    data = response.json()
    assert "characters" in data
    assert len(data["characters"]) == 8


def test_start_quiz():
    response = client.post("/api/quiz/start", json={
        "semester": "grade1-spring",
        "lessons": ["第一课：春天来了"],
        "count": 4,
        "mode_mix": 0.5
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["total"] == 4
    assert len(data["characters"]) == 4


def test_quiz_flow():
    # Start quiz
    start = client.post("/api/quiz/start", json={
        "semester": "grade1-spring",
        "lessons": ["第一课：春天来了"],
        "count": 2
    })
    assert start.status_code == 200
    session_id = start.json()["session_id"]

    # Get session
    session = client.get(f"/api/quiz/session/{session_id}")
    assert session.status_code == 200
    assert session.json()["session_id"] == session_id

    # Submit results
    submit1 = client.post("/api/quiz/submit", json={
        "session_id": session_id,
        "index": 0,
        "result": "mastered"
    })
    assert submit1.status_code == 200

    submit2 = client.post("/api/quiz/submit", json={
        "session_id": session_id,
        "index": 1,
        "result": "not_mastered"
    })
    assert submit2.status_code == 200

    # Finish
    finish = client.post("/api/quiz/finish", json={
        "session_id": session_id
    })
    assert finish.status_code == 200
    data = finish.json()
    assert data["success"] is True
    assert data["summary"]["mastered"] == 1
    assert data["summary"]["not_mastered"] == 1


def test_get_mistakes():
    response = client.get("/api/mistakes")
    assert response.status_code == 200
    assert "mistakes" in response.json()


def test_get_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "streak_days" in response.json()
