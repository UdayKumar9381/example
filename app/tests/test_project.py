def test_create_project_success(client):
    response = client.post(
        "/api/v1/projects",
        json={"name": "New Project", "description": "Project Description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Project"
    assert data["description"] == "Project Description"
    assert "id" in data


def test_create_project_missing_name(client):
    response = client.post(
        "/api/v1/projects",
        json={"description": "Missing name field"}
    )
    assert response.status_code == 422


def test_create_project_empty_name(client):
    response = client.post(
        "/api/v1/projects",
        json={"name": "", "description": "Empty name"}
    )
    assert response.status_code == 422


def test_get_project_success(client, sample_project):
    project_id = sample_project["id"]
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    assert response.json()["id"] == project_id


def test_get_project_not_found(client):
    response = client.get("/api/v1/projects/99999")
    assert response.status_code == 404


def test_get_all_projects(client, sample_project):
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert "projects" in data
    assert "total" in data
    assert data["total"] >= 1


def test_update_project_success(client, sample_project):
    project_id = sample_project["id"]
    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Project"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Project"


def test_delete_project_success(client, sample_project):
    project_id = sample_project["id"]
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204