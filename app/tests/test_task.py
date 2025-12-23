import pytest


@pytest.fixture
def sample_task(client, sample_project):
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Test Task",
            "description": "Test Description",
            "project_id": sample_project["id"]
        }
    )
    return response.json()


def test_create_task_success(client, sample_project):
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "New Task",
            "description": "Task Description",
            "project_id": sample_project["id"],
            "assignee": "john.doe@company.com"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["status"] == "TODO"
    assert data["assignee"] == "john.doe@company.com"


def test_create_task_missing_title(client, sample_project):
    response = client.post(
        "/api/v1/tasks",
        json={
            "description": "Missing title",
            "project_id": sample_project["id"]
        }
    )
    assert response.status_code == 422


def test_create_task_invalid_project(client):
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Task",
            "project_id": 99999
        }
    )
    assert response.status_code == 400


def test_get_task_success(client, sample_task):
    task_id = sample_task["id"]
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_task_not_found(client):
    response = client.get("/api/v1/tasks/99999")
    assert response.status_code == 404


def test_get_all_tasks(client, sample_task):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
    assert "total" in data


def test_get_tasks_by_project(client, sample_task, sample_project):
    response = client.get(f"/api/v1/tasks?project_id={sample_project['id']}")
    assert response.status_code == 200
    assert response.json()["total"] >= 1


def test_update_task_status_success(client, sample_task):
    task_id = sample_task["id"]
    response = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "IN_PROGRESS"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "IN_PROGRESS"


def test_update_task_status_invalid(client, sample_task):
    task_id = sample_task["id"]
    response = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "INVALID_STATUS"}
    )
    assert response.status_code == 422


def test_assign_task_success(client, sample_task):
    task_id = sample_task["id"]
    response = client.patch(
        f"/api/v1/tasks/{task_id}/assignee",
        json={"assignee": "jane.doe@company.com"}
    )
    assert response.status_code == 200
    assert response.json()["assignee"] == "jane.doe@company.com"


def test_delete_task_success(client, sample_task):
    task_id = sample_task["id"]
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204


def test_task_status_workflow(client, sample_task):
    task_id = sample_task["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "IN_PROGRESS"}
    )
    assert response.json()["status"] == "IN_PROGRESS"

    response = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "IN_REVIEW"}
    )
    assert response.json()["status"] == "IN_REVIEW"

    response = client.patch(
        f"/api/v1/tasks/{task_id}/status",
        json={"status": "DONE"}
    )
    assert response.json()["status"] == "DONE"