"""FSM states for Telegram bot conversations."""

from aiogram.fsm.state import State, StatesGroup


class AddRepoStates(StatesGroup):
    """States for /addrepo command flow."""

    waiting_for_url = State()


class StudyStates(StatesGroup):
    """States for /study command flow."""

    selecting_topic = State()
    answering_question = State()


class RemoveRepoStates(StatesGroup):
    """States for /removerepo command flow."""

    selecting_repo = State()
    confirming_removal = State()
