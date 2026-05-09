from pydantic import BaseModel, Field


class AnswerRecordRequest(BaseModel):
    target_character: str
    target_pinyin: str
    selected_character: str | None = None
    selected_pinyin: str | None = None
    is_correct: bool
    similarity: float | None = None


class QuizAttemptCreateRequest(BaseModel):
    user_id: int
    hsk_level: str
    difficulty: str
    score: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=1)
    answers: list[AnswerRecordRequest]


class QuizAttemptResponse(BaseModel):
    id: int
    user_id: int
    hsk_level: str
    difficulty: str
    score: int
    total_questions: int
    created_at: str


class MistakeResponse(BaseModel):
    character: str
    target_pinyin: str
    mistakes: int


class ProgressSummaryResponse(BaseModel):
    user_id: int
    total_quizzes: int
    total_questions: int
    correct_answers: int
    accuracy: float
    most_missed_characters: list[MistakeResponse]