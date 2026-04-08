class TestCourseRecordCreate:
    def test_create_course_record(self, client, sample_student):
        resp = client.post("/api/course-records", json={
            "student_id": sample_student["id"],
            "course_code": "C2024001",
            "assessment": "Good progress in calculus",
            "objective": "Master differentiation",
            "teacher": "Prof. Wang",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["student_id"] == sample_student["id"]
        assert data["course_code"] == "C2024001"
        assert data["assessment"] == "Good progress in calculus"
        assert "id" in data

    def test_create_course_record_student_not_found(self, client):
        resp = client.post("/api/course-records", json={
            "student_id": 99999,
            "course_code": "C9999",
            "assessment": "Test",
        })
        assert resp.status_code == 404


class TestCourseRecordRead:
    def test_list_all_course_records(self, client, sample_course_record):
        resp = client.get("/api/course-records")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_list_course_records_by_student(self, client, sample_student, sample_course_record):
        resp = client.get(f"/api/course-records?student_id={sample_student['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert all(r["student_id"] == sample_student["id"] for r in data)

    def test_get_course_record_by_id(self, client, sample_course_record):
        resp = client.get(f"/api/course-records/{sample_course_record['id']}")
        assert resp.status_code == 200
        assert resp.json()["course_code"] == sample_course_record["course_code"]

    def test_get_course_record_not_found(self, client):
        resp = client.get("/api/course-records/99999")
        assert resp.status_code == 404


class TestCourseRecordUpdate:
    def test_update_course_record(self, client, sample_course_record):
        resp = client.put(f"/api/course-records/{sample_course_record['id']}", json={
            "assessment": "Excellent progress",
            "teacher": "Prof. Zhang",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["assessment"] == "Excellent progress"
        assert data["teacher"] == "Prof. Zhang"

    def test_update_course_record_not_found(self, client):
        resp = client.put("/api/course-records/99999", json={
            "assessment": "N/A",
        })
        assert resp.status_code == 404
