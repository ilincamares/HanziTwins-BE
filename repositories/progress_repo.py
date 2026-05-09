from sqlalchemy.orm import Session

from database.models import QuizAttempt, AnswerRecord


class ProgressRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_attempts_for_user(self, user_id: int) -> list[type[QuizAttempt]]:
        return (
            self.db.query(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id)
            .order_by(QuizAttempt.created_at.desc())
            .all()
        )

    def get_wrong_answers_for_user(self, user_id: int) -> list[type[AnswerRecord]]:
        return (
            self.db.query(AnswerRecord)
            .join(QuizAttempt)
            .filter(QuizAttempt.user_id == user_id)
            .filter(AnswerRecord.is_correct.is_(False))
            .order_by(AnswerRecord.created_at.desc())
            .all()
        )

    def get_most_missed_characters(self, user_id: int) -> list[dict]:
        wrong_answers = self.get_wrong_answers_for_user(user_id)

        mistake_counter = {}

        for answer in wrong_answers:
            character = answer.target_character

            if character not in mistake_counter:
                mistake_counter[character] = {
                    "character": character,
                    "target_pinyin": answer.target_pinyin,
                    "mistakes": 0,
                }

            mistake_counter[character]["mistakes"] += 1

        return sorted(
            mistake_counter.values(),
            key=lambda item: item["mistakes"],
            reverse=True
        )

    def get_progress_summary(self, user_id: int) -> dict:
        attempts = self.get_attempts_for_user(user_id)

        total_quizzes = len(attempts)
        total_questions = sum(attempt.total_questions for attempt in attempts)
        correct_answers = sum(attempt.score for attempt in attempts)

        if total_questions == 0:
            accuracy = 0.0
        else:
            accuracy = round((correct_answers / total_questions) * 100, 2)

        return {
            "user_id": user_id,
            "total_quizzes": total_quizzes,
            "total_questions": total_questions,
            "correct_answers": correct_answers,
            "accuracy": accuracy,
            "most_missed_characters": self.get_most_missed_characters(user_id),
        }