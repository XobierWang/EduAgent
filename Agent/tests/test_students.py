class TestStudentCreate:
    def test_create_student(self, client):
        resp = client.post("/api/students", json={
            "student_code": "S2024001",
            "full_name": "张三",
            "gender": "男",
            "phone": "13800001111",
            "id_number": "310101200501011234",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["student_code"] == "S2024001"
        assert data["full_name"] == "张三"
        assert data["gender"] == "男"
        assert "id" in data
        assert "created_at" in data

    def test_create_duplicate_student_code(self, client, sample_student):
        resp = client.post("/api/students", json={
            "student_code": sample_student["student_code"],
            "full_name": "李四",
        })
        assert resp.status_code == 409
        assert "already exists" in resp.json()["detail"]


class TestStudentRead:
    def test_list_students(self, client, sample_student):
        resp = client.get("/api/students")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        codes = [s["student_code"] for s in data]
        assert sample_student["student_code"] in codes

    def test_get_student_by_id(self, client, sample_student):
        resp = client.get(f"/api/students/{sample_student['id']}")
        assert resp.status_code == 200
        assert resp.json()["student_code"] == sample_student["student_code"]

    def test_get_student_not_found(self, client):
        resp = client.get("/api/students/99999")
        assert resp.status_code == 404


class TestStudentUpdate:
    def test_update_student(self, client, sample_student):
        resp = client.put(f"/api/students/{sample_student['id']}", json={
            "full_name": "张三（更新）",
            "phone": "13900001111",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["full_name"] == "张三（更新）"
        assert data["phone"] == "13900001111"

    def test_update_student_not_found(self, client):
        resp = client.put("/api/students/99999", json={
            "full_name": "不存在",
        })
        assert resp.status_code == 404
