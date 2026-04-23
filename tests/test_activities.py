"""Tests for the activities API endpoints using AAA (Arrange-Act-Assert) pattern."""
import pytest


class TestGetActivities:
    """Test suite for GET /activities endpoint."""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Verify that GET /activities returns all registered activities.
        
        AAA Pattern:
        - Arrange: reset_activities fixture sets up a known state
        - Act: make GET request to /activities
        - Assert: verify response contains all activities
        """
        # Arrange (implicit via reset_activities fixture)

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

    def test_get_activities_includes_activity_details(self, client, reset_activities):
        """Verify that activity details include all required fields.
        
        AAA Pattern:
        - Arrange: reset_activities fixture provides known data
        - Act: fetch activities from API
        - Assert: verify structure and content of response
        """
        # Arrange
        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club

    def test_get_activities_includes_participant_count(self, client, reset_activities):
        """Verify that activity details include current participant data.
        
        AAA Pattern:
        - Arrange: known activities with participants
        - Act: retrieve activities
        - Assert: verify participant list is correct
        """
        # Arrange
        # Act
        response = client.get("/activities")

        # Assert
        data = response.json()
        chess_club = data["Chess Club"]
        assert len(chess_club["participants"]) == 2
        assert "michael@mergington.edu" in chess_club["participants"]
        assert "daniel@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_student_succeeds(self, client, reset_activities):
        """Verify that a new student can successfully sign up for an activity.
        
        AAA Pattern:
        - Arrange: define new student email and activity name
        - Act: POST signup request
        - Assert: verify response indicates success
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert f"Signed up {email}" in response.json()["message"]

    def test_signup_persists_in_activities_list(self, client, reset_activities):
        """Verify that signup persists participant in the activities data.
        
        AAA Pattern:
        - Arrange: prepare new student data
        - Act: execute signup and retrieve activities
        - Assert: verify student appears in participants list
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Programming Class"
        from src.app import activities

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        activities_data = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert email in activities_data[activity_name]["participants"]

    def test_signup_duplicate_student_fails(self, client, reset_activities):
        """Verify that duplicate signup attempt is rejected.
        
        AAA Pattern:
        - Arrange: use existing participant email
        - Act: attempt signup for same activity
        - Assert: verify 400 error with appropriate message
        """
        # Arrange
        email = "michael@mergington.edu"  # Already signed up for Chess Club
        activity_name = "Chess Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_different_activity_same_student_succeeds(self, client, reset_activities):
        """Verify that a student can sign up for multiple different activities.
        
        AAA Pattern:
        - Arrange: use existing participant who is only in one activity
        - Act: sign them up for a different activity
        - Assert: verify signup succeeds
        """
        # Arrange
        email = "michael@mergington.edu"
        new_activity = "Programming Class"

        # Act
        response = client.post(
            f"/activities/{new_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert email in client.get("/activities").json()[new_activity]["participants"]

    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """Verify that signup for nonexistent activity returns 404.
        
        AAA Pattern:
        - Arrange: define invalid activity name
        - Act: attempt signup
        - Assert: verify 404 error
        """
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Nonexistent Club"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_invalid_email_format_fails(self, client, reset_activities):
        """Verify that invalid email formats are rejected.
        
        AAA Pattern:
        - Arrange: prepare emails without @ or domain
        - Act: attempt signup with invalid emails
        - Assert: verify 400 error for each invalid format
        """
        # Arrange
        invalid_emails = ["invalidemail", "user@", "@domain.com", "user domain@test.com"]
        activity_name = "Chess Club"

        # Act & Assert
        for invalid_email in invalid_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": invalid_email}
            )
            assert response.status_code == 400
            assert "Invalid email format" in response.json()["detail"]

    def test_signup_at_capacity_fails(self, client, reset_activities):
        """Verify that signup fails when activity reaches max capacity.
        
        AAA Pattern:
        - Arrange: fill activity to max_participants
        - Act: attempt signup beyond capacity
        - Assert: verify 400 error indicating activity is full
        """
        # Arrange
        from src.app import activities
        activity_name = "Chess Club"
        activity = activities[activity_name]
        max_cap = activity["max_participants"]
        # Fill the activity to capacity
        activity["participants"] = [f"student{i}@mergington.edu" for i in range(max_cap)]
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestRemoveParticipant:
    """Test suite for DELETE /activities/{activity_name}/participants endpoint."""

    def test_remove_participant_succeeds(self, client, reset_activities):
        """Verify that a participant can be successfully removed from an activity.
        
        AAA Pattern:
        - Arrange: identify existing participant
        - Act: send DELETE request
        - Assert: verify removal and success message
        """
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        from src.app import activities
        initial_count = len(activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert f"Removed {email}" in response.json()["message"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
        assert email not in activities[activity_name]["participants"]

    def test_remove_participant_reflects_in_activities(self, client, reset_activities):
        """Verify that participant removal reflects in subsequent API calls.
        
        AAA Pattern:
        - Arrange: get initial activities state
        - Act: remove participant and fetch activities again
        - Assert: verify participant no longer in list
        """
        # Arrange
        email = "emma@mergington.edu"
        activity_name = "Programming Class"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        updated_activities = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert email not in updated_activities[activity_name]["participants"]

    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """Verify that removing a nonexistent participant returns 404.
        
        AAA Pattern:
        - Arrange: define participant not in activity
        - Act: attempt removal
        - Assert: verify 404 error
        """
        # Arrange
        email = "doesnotexist@mergington.edu"
        activity_name = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """Verify that removing from nonexistent activity returns 404.
        
        AAA Pattern:
        - Arrange: define invalid activity name
        - Act: attempt removal
        - Assert: verify 404 error
        """
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Nonexistent Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_same_participant_twice_fails(self, client, reset_activities):
        """Verify that removing the same participant twice fails on second attempt.
        
        AAA Pattern:
        - Arrange: identify participant to remove twice
        - Act: first removal succeeds, second removal attempted
        - Assert: first succeeds (200), second fails (404)
        """
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"

        # Act
        first_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )
        second_response = client.delete(
            f"/activities/{activity_name}/participants",
            params={"email": email}
        )

        # Assert
        assert first_response.status_code == 200
        assert second_response.status_code == 404
        assert "Participant not found" in second_response.json()["detail"]
