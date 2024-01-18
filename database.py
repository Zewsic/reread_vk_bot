from sqlalchemy import Column, Integer, String, create_engine, ForeignKey, Date, Time, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.sql import exists
from typing import Any

import config

if config.DataBase.TYPE == "sqlite":
    engine = create_engine(f'sqlite:///{config.DataBase.SQLITE_PATH}', echo=True)
    Session = sessionmaker(bind=engine)
    Base = declarative_base()
else:
    engine = None
    Session = None
    Base = None


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    vk_id = Column(Integer, unique=True, nullable=False)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    domain = Column(String)
    role = Column(String, nullable=False)
    isBanned = Column(Boolean, nullable=False)
    ban_reason = Column(String)
    voted = Column(Boolean, nullable=True)
    expert_nominations = Column(String, nullable=True)
    accepted_rules = Column(Integer, nullable=True, default=None)


class ContestMember(Base):
    __tablename__ = 'contest_members'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    user_id = Column(Integer, unique=True, nullable=False)


class UserContest(Base):
    __tablename__ = 'user_contests'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    member_id = Column(Integer, nullable=False)
    text_id = Column(Integer, nullable=False)
    contest_id = Column(Integer, nullable=False)

    name = Column(String)
    school = Column(String)
    email = Column(String)
    teacher = Column(String)
    phone_number = Column(String)

    nomination_id = Column(Integer, nullable=False)
    group_id = Column(Integer, nullable=False)

    started = Column(Integer)
    deadline = Column(Integer)
    finished = Column(Integer)
    sended_work = Column(String)

    isChecking = Column(Boolean)
    isApproved = Column(Boolean)
    declined_reason = Column(String)

    isBanned = Column(Boolean, nullable=False)
    ban_reason = Column(String)

    canSendWork = Column(Boolean, nullable=False)
    user_votes = Column(Integer, nullable=False)


class UserContestRate(Base):
    __tablename__ = 'user_contest_rates'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)

    user_contest_id = Column(Integer, nullable=False)
    expert_id = Column(Integer, nullable=False)
    feedback = Column(String, nullable=False)
    voted_by_admin = Column(Boolean, nullable=False, default=False)


class UserContestRateValue(Base):
    __tablename__ = 'user_contest_rates_values'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    user_contest_rate_id = Column(Integer, nullable=False)
    contest_rate_id = Column(Integer, nullable=False)
    rate_value = Column(Integer)


class Contest(Base):
    __tablename__ = 'contests'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    start_date = Column(Integer)
    finish_date = Column(Integer)
    rates_date = Column(Integer)
    winners_date = Column(Integer)
    time_for_send = Column(Integer)
    price = Column(Integer)


class ContestRateType(Base):
    __tablename__ = 'contest_rate_types'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String)
    min_value = Column(Integer)
    max_value = Column(Integer)


class ContestNomination(Base):
    __tablename__ = 'contest_nominations'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String)


class ContestGroup(Base):
    __tablename__ = 'contest_groups'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String)


class ContextText(Base):
    __tablename__ = 'contest_texts'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True, nullable=False)
    name = Column(String, nullable=False)
    author = Column(String, nullable=False)
    text = Column(String, nullable=False)
    nomination_id = Column(Integer, nullable=False)
    group_id = Column(Integer, nullable=False)


Base.metadata.create_all(engine)
