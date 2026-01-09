"""Tests for FSM states."""

from aiogram.fsm.state import State

from study_agent.presentation.telegram.states import (
    AddRepoStates,
    RemoveRepoStates,
    StudyStates,
)


class TestAddRepoStates:
    """Tests for AddRepoStates."""

    def test_waiting_for_url_is_state(self):
        """Test that waiting_for_url is a State."""
        assert isinstance(AddRepoStates.waiting_for_url, State)

    def test_state_group_name(self):
        """Test state group name."""
        assert AddRepoStates.__name__ == "AddRepoStates"


class TestStudyStates:
    """Tests for StudyStates."""

    def test_selecting_topic_is_state(self):
        """Test that selecting_topic is a State."""
        assert isinstance(StudyStates.selecting_topic, State)

    def test_answering_question_is_state(self):
        """Test that answering_question is a State."""
        assert isinstance(StudyStates.answering_question, State)

    def test_state_group_name(self):
        """Test state group name."""
        assert StudyStates.__name__ == "StudyStates"


class TestRemoveRepoStates:
    """Tests for RemoveRepoStates."""

    def test_selecting_repo_is_state(self):
        """Test that selecting_repo is a State."""
        assert isinstance(RemoveRepoStates.selecting_repo, State)

    def test_confirming_removal_is_state(self):
        """Test that confirming_removal is a State."""
        assert isinstance(RemoveRepoStates.confirming_removal, State)

    def test_state_group_name(self):
        """Test state group name."""
        assert RemoveRepoStates.__name__ == "RemoveRepoStates"
