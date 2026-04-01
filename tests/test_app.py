import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Ensure tests do not leak mutations to the in-memory activities store."""
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_all_expected_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()

    assert set(data.keys()) == set(activities.keys())

    expected_fields = {"description", "schedule", "max_participants", "participants"}
    for activity_name in activities:
        assert expected_fields.issubset(data[activity_name].keys())


def test_signup_for_activity_success():
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_not_found():
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_for_activity_duplicate_student():
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": existing_email}
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}


def test_unregister_from_activity_success():
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": existing_email}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {existing_email} from {activity_name}"
    }
    assert existing_email not in activities[activity_name]["participants"]


def test_unregister_from_activity_not_found_activity():
    response = client.delete(
        "/activities/Nonexistent Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_from_activity_student_not_signed_up():
    response = client.delete(
        "/activities/Chess Club/signup",
        params={"email": "not_enrolled@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student not found in activity"}


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"
