from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship

from database.connection import Base


def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    quiz_attempts = relationship(
        'QuizAttempt',
        back_populates='user',
        cascade='all, delete-orphan',
    )

class QuizAttempt(Base):
    __tablename__ = 'quiz_attempts'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    hsk_level = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship(
        'User',
        back_populates='quiz_attempts',
    )

    answers = relationship(
        'AnswerRecord',
        back_populates='attempt',
        cascade='all, delete-orphan',
    )

class AnswerRecord(Base):
    __tablename__ = 'answer_records'

    id = Column(Integer, primary_key=True, index=True)
    attempt_id = Column(Integer, ForeignKey('quiz_attempts.id'), nullable=False)
    target_character = Column(String, nullable=False)
    target_pinyin = Column(String, nullable=False)
    selected_character = Column(String, nullable=False)
    selected_pinyin = Column(String, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    similarity = Column(Float, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    attempt = relationship(
        'QuizAttempt',
        back_populates='answers',
    )