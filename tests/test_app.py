import pytest
from fastapi.testclient import TestClient
from src.app import app, activities
import copy

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state after each test"""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)

def test_root_redirect():
    """Test that root endpoint redirects to static index.html"""
    # Arrange
    # (No special setup needed)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"

def test_get_activities():
    """Test getting all activities"""
    # Arrange
    # (Activities are set up by fixture)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # Based on the initial activities
    assert "Chess Club" in data
    assert "Programming Class" in data
    # Check structure of one activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)

def test_signup_success():
    """Test successful signup for an activity"""
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    # Verify added to participants
    assert email in activities[activity_name]["participants"]

def test_signup_activity_not_found():
    """Test signup for non-existent activity"""
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.post("/activities/NonExistent/signup?email={email}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]

def test_signup_already_signed_up():
    """Test signup when student is already signed up"""
    # Arrange
    activity_name = "Programming Class"
    email = "emma@mergington.edu"  # Already in participants

    # Act
    response = client.post(f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Student already signed up for this activity" in data["detail"]

def test_signup_activity_full():
    """Test signup when activity is full"""
    # Arrange
    activity_name = "Basketball"
    # Basketball has max 16, starts with 1 participant, so add 15 more to fill
    for i in range(15):
        client.post(f"/activities/{activity_name}/signup?email=user{i}@mergington.edu")

    # Act - try to add one more
    response = client.post(f"/activities/{activity_name}/signup?email=extra@mergington.edu")

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Activity is full" in data["detail"]

def test_unregister_success():
    """Test successful unregistration from an activity"""
    # Arrange
    activity_name = "Gym Class"
    email = "john@mergington.edu"  # Already in participants

    # Act
    response = client.delete(f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert activity_name in data["message"]
    # Verify removed from participants
    assert email not in activities[activity_name]["participants"]

def test_unregister_activity_not_found():
    """Test unregister from non-existent activity"""
    # Arrange
    email = "student@mergington.edu"

    # Act
    response = client.delete("/activities/NonExistent/signup?email={email}")

    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]

def test_unregister_not_signed_up():
    """Test unregister when student is not signed up"""
    # Arrange
    activity_name = "Basketball"
    email = "newsstudent@mergington.edu"  # Not in participants

    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Student not signed up for this activity" in data["detail"]