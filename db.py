from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker


DATABASE_NAME = 'terpila.sqlite'

engine = create_engine(f"sqlite:///{DATABASE_NAME}")
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()


class Users(Base):
    __tablename__ = 'Clients'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer)
    first_name = Column(String(100), nullable=True)
    username = Column(String(50), nullable=True)
    name = Column(String(50), nullable=False)
    phnum = Column(String(50), nullable=False)


class Application(Base):
    __tablename__ = 'applications'
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, nullable=False)
    location = Column(String, nullable=True)
    photo = Column(String, nullable=True)
    reason = Column(String, nullable=False)


def add_user(id, first_name, username, name, phnum):
    session = Session()
    exist = check_existing(id)
    if not exist:
        user = Users(chat_id=id,
                       first_name=first_name,
                       username=username,
                       name=name,
                       phnum=phnum)
        session.add(user)
        session.commit()
    session.close()


def add_application(chat_id, location, photo, reason):
    session = Session()
    application = Application(chat_id=chat_id, location=location, photo=photo, reason=reason)
    session.add(application)
    session.commit()
    session.close()


def update_user(chat_id, name=None, phnum=None):
    session = Session()
    user = session.query(Users).filter_by(chat_id=chat_id).first()
    if user:
        if name is not None:
            user.name = name
        if phnum is not None:
            user.phnum = phnum
        session.commit()
    session.close()


def get_user_info(chat_id):
    session = Session()
    user = session.query(Users).filter_by(chat_id=chat_id).first()
    if user:
        user_info = {
            'name': user.name,
            'phnum': user.phnum
        }
        return user_info
    return None


def check_existing(id):
    session = Session()
    result = session.query(Users.chat_id).filter(Users.chat_id == id).all()
    return result


def create_db():
    Base.metadata.create_all(engine)
    session = Session()
    session.commit()


if __name__ == '__main__':
    create_db()