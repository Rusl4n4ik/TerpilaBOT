from aiogram.dispatcher.filters.state import StatesGroup, State


class Users(StatesGroup):
    Name = State()
    Phnum = State()


class Application(StatesGroup):
    Location = State()
    Media = State()
    Reason = State()
    Suggestion = State()
    Suggestion_ph = State()


class Contact(StatesGroup):
    Number = State()
    Text = State()


class Update(StatesGroup):
    Name = State()
    Phnum = State()