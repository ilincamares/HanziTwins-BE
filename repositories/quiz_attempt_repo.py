from sqlalchemy.orm import Session

from database.models import QuizAttempt, AnswerRecord


class QuizAttemptRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_attempt(
        self,
        user_id: int,
        hsk_level: str,
        difficulty: str,
        score: int,
        total_questions: int,
        answers: list[dict],
    ) -> QuizAttempt:
        attempt = QuizAttempt(
            user_id=user_id,
            hsk_level=hsk_level,
            difficulty=difficulty,
            score=score,
            total_questions=total_questions,
        )

        self.db.add(attempt)
        self.db.commit()
        self.db.refresh(attempt)

        for answer in answers:
            answer_record = AnswerRecord(
                attempt_id=attempt.id,
                target_character=answer["target_character"],
                target_pinyin=answer["target_pinyin"],
                selected_character=answer.get("selected_character"),
                selected_pinyin=answer.get("selected_pinyin"),
                is_correct=answer["is_correct"],
                similarity=answer.get("similarity"),
            )

            self.db.add(answer_record)

        self.db.commit()
        self.db.refresh(attempt)

        return attempt

    def get_by_id(self, attempt_id: int) -> QuizAttempt | None:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.id == attempt_id)
            .first()
        )

    def get_by_user_id(self, user_id: int) -> list[type[QuizAttempt]]:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )