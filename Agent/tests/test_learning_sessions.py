class TestLearningSessionCreate:
    def test_create_learning_session(self, client, sample_student):
        resp = client.post("/api/learning-sessions", json={
            "student_id": sample_student["id"],
            "session_code": "LS2024001",
            "session_type": "tutorial",
            "teacher_name": "Prof. Li",
            "department": "Mathematics",
            "session_time": "2024-03-15T14:00:00",
            "summary": "Reviewed differential equations",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["student_id"] == sample_student["id"]
        assert data["session_code"] == "LS2024001"
        assert data["session_type"] == "tutorial"
        assert "id" in data

    def test_create_learning_session_student_not_found(self, client):
        resp = client.post("/api/learning-sessions", json={
            "student_id": 99999,
            "session_code": "LS9999",
            "session_type": "lecture",
        })
        assert resp.status_code == 404


class TestLearningSessionRead:
    def test_list_all_learning_sessions(self, client, sample_learning_session):
        resp = client.get("/api/learning-sessions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_list_learning_sessions_by_student(self, client, sample_student, sample_learning_session):
        resp = client.get(f"/api/learning-sessions?student_id={sample_student['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["student_id"] == sample_student["id"] for r in data)

    def test_get_learning_session_by_id(self, client, sample_learning_session):
        resp = client.get(f"/api/learning-sessions/{sample_learning_session['id']}")
        assert resp.status_code == 200
        assert resp.json()["session_code"] == sample_learning_session["session_code"]

    def test_get_learning_session_not_found(self, client):
        resp = client.get("/api/learning-sessions/99999")
        assert resp.status_code == 404


class TestLearningSessionUpdate:
    def test_update_learning_session(self, client, sample_learning_session):
        resp = client.put(f"/api/learning-sessions/{sample_learning_session['id']}", json={
            "summary": "Updated summary after review",
            "teacher_name": "Prof. Liu",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["summary"] == "Updated summary after review"

    def test_update_learning_session_not_found(self, client):
        resp = client.put("/api/learning-sessions/99999", json={
            "summary": "N/A",
        })
        assert resp.status_code == 404
