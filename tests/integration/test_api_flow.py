import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.database.base import Base
from app.database.connection import get_db
from app.main import app

from sqlalchemy.pool import StaticPool

# In-memory SQLite for testing with StaticPool so all connections share the same memory DB
TEST_DATABASE_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def test_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_full_user_flow():
    # 1. Register
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"email": "tester@example.com", "password": "securepassword123"},
    )
    assert reg_res.status_code == 200, reg_res.text
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get current user
    me_res = client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "tester@example.com"

    # 3. Create project
    proj_res = client.post(
        "/api/v1/projects",
        json={"name": "Audio Products", "description": "Customer feedback on headphones"},
        headers=headers,
    )
    assert proj_res.status_code == 201
    project_id = proj_res.json()["id"]

    # 4. Upload CSV
    csv_content = (
        'review,rating,date,source,product,category\n'
        '"Amazing sound quality and battery life!",5,2026-09-01,Amazon,Headphones,Audio\n'
        '"Terrible experience, arrived broken and support was awful.",1,2026-09-02,Website,Headphones,Audio\n'
        '"Average product, nothing special.",3,2026-09-03,Retail,Headphones,Audio\n'
    )
    file_obj = io.BytesIO(csv_content.encode("utf-8"))
    upload_res = client.post(
        "/api/v1/reviews/upload",
        data={"project_id": str(project_id)},
        files={"file": ("test.csv", file_obj, "text/csv")},
        headers=headers,
    )
    assert upload_res.status_code == 200, upload_res.text
    summary = upload_res.json()
    assert summary["imported_rows"] == 3
    assert summary["valid_rows"] == 3

    # 5. Run sentiment batch
    batch_res = client.post(
        "/api/v1/sentiment/batch",
        json={"project_id": project_id},
        headers=headers,
    )
    assert batch_res.status_code == 200
    assert batch_res.json()["processed"] == 3

    # 6. Analytics Summary
    sum_res = client.get(f"/api/v1/analytics/summary?project_id={project_id}", headers=headers)
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["total_reviews"] == 3
    assert sum_data["analyzed_reviews"] == 3
    assert sum_data["positive"] >= 1
    assert sum_data["negative"] >= 1

    # 7. Analytics Trends & Distribution & Insights
    trends_res = client.get(f"/api/v1/analytics/trends?project_id={project_id}", headers=headers)
    assert trends_res.status_code == 200
    dist_res = client.get(f"/api/v1/analytics/distribution?project_id={project_id}", headers=headers)
    assert dist_res.status_code == 200
    insights_res = client.get(f"/api/v1/analytics/insights?project_id={project_id}", headers=headers)
    assert insights_res.status_code == 200

    # 8. List reviews with filters
    rev_res = client.get(f"/api/v1/reviews?project_id={project_id}&sentiment=Positive", headers=headers)
    assert rev_res.status_code == 200
    reviews_list = rev_res.json()["items"]
    assert len(reviews_list) >= 1
    review_id = reviews_list[0]["id"]

    # 8b. Get single review detail
    detail_res = client.get(f"/api/v1/reviews/{review_id}?project_id={project_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == review_id
    assert detail_res.json()["sentiment"] is not None

    # 8c. Flag review
    flag_res = client.post(f"/api/v1/reviews/{review_id}/flag?project_id={project_id}", headers=headers)
    assert flag_res.status_code == 200
    assert flag_res.json()["flagged"] is True

    # 9. Single sentiment test
    single_res = client.post(
        "/api/v1/sentiment/analyze",
        json={"text": "Outstanding and wonderful experience!"},
        headers=headers,
    )
    assert single_res.status_code == 200
    assert single_res.json()["sentiment"] == "Positive"

    # 10. Model info
    model_res = client.get("/api/v1/sentiment/model", headers=headers)
    assert model_res.status_code == 200
    assert "name" in model_res.json()

    # 11. Export CSV
    export_res = client.get(f"/api/v1/reviews/export?project_id={project_id}", headers=headers)
    assert export_res.status_code == 200
    assert "text/csv" in export_res.headers.get("content-type", "")

    # 12. Delete project
    del_res = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert del_res.status_code == 204


def test_auth_validation():
    # Duplicate registration
    client.post(
        "/api/v1/auth/register",
        json={"email": "unique@example.com", "password": "password123"},
    )
    dup = client.post(
        "/api/v1/auth/register",
        json={"email": "unique@example.com", "password": "password123"},
    )
    assert dup.status_code == 409

    # Wrong password login
    wrong = client.post(
        "/api/v1/auth/login",
        json={"email": "unique@example.com", "password": "wrongpassword"},
    )
    assert wrong.status_code == 401
