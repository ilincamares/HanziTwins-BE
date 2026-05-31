import random

from repositories import UserRepository, QuizAttemptRepository, ProgressRepository
from dtos.progress_dtos import QuizAttemptCreateRequest
from fastapi import Query

from services.utils import get_safe_pinyin, get_difficulty_start_index, get_safe_similarity, get_confusion_map


class ProgressService:
    def __init__(self, user_repository: UserRepository, quiz_attempt_repository: QuizAttemptRepository, progress_repository: ProgressRepository):
        self.user_repository = user_repository
        self.quiz_attempt_repository = quiz_attempt_repository
        self.progress_repository = progress_repository

    def generate_review_quiz(
        self,
        user_id: int,
        count: int,
        difficulty: str,
    ):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        if count < 1:
            raise ValueError("Number of review questions must be greater than 0.")

        difficulty = difficulty.lower()

        if difficulty not in ["easy", "medium", "hard"]:
            raise ValueError("Difficulty must be easy, medium or hard.")

        missed_characters = self.progress_repository.get_most_missed_characters(user_id)

        if not missed_characters:
            raise ValueError("No mistakes available for review.")

        confusion_map = get_confusion_map("all")

        selected_mistakes = missed_characters[:count]

        questions = []

        for mistake in selected_mistakes:
            target = mistake["character"]

            question = self.build_review_question(
                target=target,
                confusion_map=confusion_map,
                difficulty=difficulty,
            )

            if question is not None:
                questions.append(question)

        if not questions:
            raise Exception("No review questions could be generated from the recorded mistakes.")

        return {
            "metadata": {
                "mode": "review",
                "hsk_level": "personal",
                "difficulty": difficulty,
                "questions_count": len(questions),
            },
            "questions": questions,
        }

    def save_quiz_attempt(
        self,
        request: QuizAttemptCreateRequest,
    ):
        user = self.user_repository.get_by_id(request.user_id)

        if user is None:
            raise LookupError("User not found.")

        if request.score > request.total_questions:
            raise ValueError("Score cannot be higher than total questions.")

        answers_as_dicts = [
            answer.model_dump()
            for answer in request.answers
        ]

        attempt = self.quiz_attempt_repository.create_attempt(
            user_id=request.user_id,
            hsk_level=request.hsk_level,
            difficulty=request.difficulty,
            score=request.score,
            total_questions=request.total_questions,
            answers=answers_as_dicts,
        )

        return {
            "id": attempt.id,
            "user_id": attempt.user_id,
            "hsk_level": attempt.hsk_level,
            "difficulty": attempt.difficulty,
            "score": attempt.score,
            "total_questions": attempt.total_questions,
            "created_at": attempt.created_at.isoformat(),
        }


    def get_progress_summary(
        self,
        user_id: int,
    ):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        return self.progress_repository.get_progress_summary(user_id)


    def get_user_attempts(
        self,
        user_id: int,
    ):
        print("Getting attempts for user")

        print("Getting user")
        print(user_id)
        user = self.user_repository.get_by_id(user_id)
        print("user found")


        if user is None:
            raise LookupError("User not found.")

        attempts = self.quiz_attempt_repository.get_by_user_id(user_id)

        return {
            "user_id": user_id,
            "attempts": [
                {
                    "id": attempt.id,
                    "hsk_level": attempt.hsk_level,
                    "difficulty": attempt.difficulty,
                    "score": attempt.score,
                    "total_questions": attempt.total_questions,
                    "created_at": attempt.created_at.isoformat(),
                }
                for attempt in attempts
            ],
        }


    def get_user_mistakes(
        self,
        user_id: int,
    ):
        user = self.user_repository.get_by_id(user_id)

        if user is None:
            raise LookupError("User not found.")

        return {
            "user_id": user_id,
            "mistakes": self.progress_repository.get_most_missed_characters(user_id),
        }

    def build_review_question(self, target: str, confusion_map: dict, difficulty: str) -> dict | None:
        if target not in confusion_map:
            return None

        neighbors_data = confusion_map.get(target, [])
        target_pinyin = get_safe_pinyin(target)

        options = [
            {
                "character": target,
                "pinyin": target_pinyin,
                "similarity": 100.0,
                "is_correct": True,
            }
        ]

        seen_pinyins = {target_pinyin}

        start_idx = get_difficulty_start_index(difficulty)
        distractors_found = 0

        for rh_char, score in neighbors_data[start_idx:]:
            rh_pinyin = get_safe_pinyin(rh_char)

            if rh_pinyin not in seen_pinyins:
                options.append(
                    {
                        "character": rh_char,
                        "pinyin": rh_pinyin,
                        "similarity": get_safe_similarity(score),
                        "is_correct": False,
                    }
                )

                seen_pinyins.add(rh_pinyin)
                distractors_found += 1

            if distractors_found == 3:
                break

        random.shuffle(options)

        return {
            "target": target,
            "target_pinyin": target_pinyin,
            "options": options,
        }