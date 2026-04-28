import sys
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def get_quiz_module():
    """
    Finds the already-imported routes_quiz module.
    """
    for module_name, module in sys.modules.items():
        if module_name.endswith("routes_quiz"):
            return module

    raise RuntimeError(
        "Could not find routes_quiz module. "
        "Make sure the quiz router is imported in main.py."
    )

def test_quiz_response_structure():
    """Verify that the objects are formatted correctly."""
    response = client.get("/api/quiz/generate?count=1")
    assert response.status_code == 200

    question = response.json()["questions"][0]

    assert "target" in question
    assert "target_pinyin" in question
    assert "options" in question

    options = question["options"]
    assert len(options) > 0

    first_option = options[0]
    assert "character" in first_option
    assert "pinyin" in first_option
    assert "similarity" in first_option
    assert "is_correct" in first_option


def test_generate_quiz_count_matches_metadata():
    """The number of returned questions should match metadata.questions_count."""
    response = client.get("/api/quiz/generate?count=3")

    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["questions_count"] == len(data["questions"])


def test_generate_quiz_each_question_has_one_correct_answer():
    """Each question should contain exactly one correct answer."""
    response = client.get("/api/quiz/generate?count=5")

    assert response.status_code == 200
    data = response.json()

    for question in data["questions"]:
        correct_options = [
            option for option in question["options"]
            if option["is_correct"] is True
        ]

        assert len(correct_options) == 1


def test_generate_quiz_correct_option_matches_target():
    """The correct option should contain the target character and target pinyin."""
    response = client.get("/api/quiz/generate?count=5")

    assert response.status_code == 200
    data = response.json()

    for question in data["questions"]:
        correct_option = next(
            option for option in question["options"]
            if option["is_correct"] is True
        )

        assert correct_option["character"] == question["target"]
        assert correct_option["pinyin"] == question["target_pinyin"]
        assert correct_option["similarity"] == 100.0


def test_generate_quiz_options_have_no_duplicate_pinyins():
    """The endpoint should not include multiple options with the same pinyin."""
    response = client.get("/api/quiz/generate?count=5")

    assert response.status_code == 200
    data = response.json()

    for question in data["questions"]:
        pinyins = [option["pinyin"] for option in question["options"]]
        assert len(pinyins) == len(set(pinyins))


def test_generate_quiz_options_count_is_between_one_and_four():
    """
    Each question should have at least the correct answer and at most
    four options total.
    """
    response = client.get("/api/quiz/generate?count=5")

    assert response.status_code == 200
    data = response.json()

    for question in data["questions"]:
        assert 1 <= len(question["options"]) <= 4


def test_generate_quiz_valid_difficulties():
    """The API should accept all supported difficulty levels."""
    for difficulty in ["easy", "medium", "hard"]:
        response = client.get(f"/api/quiz/generate?difficulty={difficulty}&count=1")

        assert response.status_code == 200
        assert response.json()["metadata"]["difficulty"] == difficulty


def test_generate_quiz_invalid_difficulty():
    """Unsupported difficulty values should be rejected."""
    response = client.get("/api/quiz/generate?difficulty=expert")

    assert response.status_code == 400
    assert "not supported" in response.json()["detail"]


def test_generate_quiz_count_zero():
    """A quiz with zero questions should be rejected."""
    response = client.get("/api/quiz/generate?count=0")

    assert response.status_code == 400
    assert "greater than 0" in response.json()["detail"]


def test_generate_quiz_count_negative():
    """A quiz with a negative question count should be rejected."""
    response = client.get("/api/quiz/generate?count=-5")

    assert response.status_code == 400
    assert "greater than 0" in response.json()["detail"]


def test_generate_quiz_count_non_integer():
    """FastAPI should reject non-integer values for count."""
    response = client.get("/api/quiz/generate?count=abc")

    assert response.status_code == 422


def test_generate_quiz_count_float():
    """FastAPI should reject floating-point values for count."""
    response = client.get("/api/quiz/generate?count=2.5")

    assert response.status_code == 422


def test_generate_quiz_hsk_zero():
    """HSK level 0 should be rejected."""
    response = client.get("/api/quiz/generate?hsk_level=0")

    assert response.status_code == 400
    assert "between 1 and 6" in response.json()["detail"]


def test_generate_quiz_hsk_too_high():
    """HSK levels above 6 should be rejected."""
    response = client.get("/api/quiz/generate?hsk_level=7")

    assert response.status_code == 400
    assert "between 1 and 6" in response.json()["detail"]


def test_generate_quiz_hsk_non_numeric():
    """Non-numeric HSK levels should be rejected, except for 'all'."""
    response = client.get("/api/quiz/generate?hsk_level=abc")

    assert response.status_code == 400
    assert "must be number" in response.json()["detail"]


def test_generate_quiz_hsk_all_uppercase():
    """
    The API should accept 'ALL' because the route normalizes hsk_level
    when loading the confusion map.
    """
    response = client.get("/api/quiz/generate?hsk_level=ALL")

    assert response.status_code == 200
    assert response.json()["metadata"]["hsk_level"] == "ALL"


def test_generate_quiz_request_more_questions_than_available(monkeypatch):
    """
    If count is larger than the available character set, the endpoint should
    return only the available number of questions.
    """
    quiz_module = get_quiz_module()

    fake_confusion_map = {
        "你": [["他", 0.9], ["们", 0.8], ["好", 0.7]],
        "好": [["你", 0.9], ["他", 0.8], ["们", 0.7]],
    }

    fake_pinyin = {
        "你": "ni",
        "好": "hao",
        "他": "ta",
        "们": "men",
    }

    monkeypatch.setattr(quiz_module, "load_confusion_map", lambda hsk_level: fake_confusion_map)
    monkeypatch.setattr(quiz_module, "CHAR_TO_PINYIN", fake_pinyin)
    monkeypatch.setattr(quiz_module.random, "sample", lambda population, k: list(population)[:k])
    monkeypatch.setattr(quiz_module.random, "shuffle", lambda options: None)

    response = client.get("/api/quiz/generate?count=10")

    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["questions_count"] == 2
    assert len(data["questions"]) == 2


def test_generate_quiz_empty_confusion_map(monkeypatch):
    """
    If the confusion map is empty, the endpoint currently returns an empty quiz.
    """
    quiz_module = get_quiz_module()

    monkeypatch.setattr(quiz_module, "load_confusion_map", lambda hsk_level: {})
    monkeypatch.setattr(quiz_module, "CHAR_TO_PINYIN", {})

    response = client.get("/api/quiz/generate?count=5")

    assert response.status_code == 200
    data = response.json()

    assert data["metadata"]["questions_count"] == 0
    assert data["questions"] == []


def test_generate_quiz_skips_duplicate_pinyins(monkeypatch):
    """
    Distractors with the same pinyin as an already selected option should
    be skipped.
    """
    quiz_module = get_quiz_module()

    fake_confusion_map = {
        "甲": [
            ["乙", 0.95],
            ["丙", 0.90],
            ["丁", 0.85],
            ["戊", 0.80],
        ]
    }

    fake_pinyin = {
        "甲": "a",
        "乙": "a",  # duplicate, should be skipped
        "丙": "b",
        "丁": "c",
        "戊": "d",
    }

    monkeypatch.setattr(quiz_module, "load_confusion_map", lambda hsk_level: fake_confusion_map)
    monkeypatch.setattr(quiz_module, "CHAR_TO_PINYIN", fake_pinyin)
    monkeypatch.setattr(quiz_module.random, "sample", lambda population, k: list(population)[:k])
    monkeypatch.setattr(quiz_module.random, "shuffle", lambda options: None)

    response = client.get("/api/quiz/generate?difficulty=hard&count=1")

    assert response.status_code == 200
    question = response.json()["questions"][0]

    option_pinyins = [option["pinyin"] for option in question["options"]]

    assert "a" in option_pinyins
    assert "b" in option_pinyins
    assert "c" in option_pinyins
    assert "d" in option_pinyins
    assert len(option_pinyins) == len(set(option_pinyins))
    assert len(question["options"]) == 4


def test_generate_quiz_uses_character_as_pinyin_fallback(monkeypatch):
    """
    If a character is missing from CHAR_TO_PINYIN, the route currently falls
    back to using the character itself as the pinyin value.
    """
    quiz_module = get_quiz_module()

    fake_confusion_map = {
        "甲": [
            ["乙", 0.95],
            ["丙", 0.90],
            ["丁", 0.85],
        ]
    }

    fake_pinyin = {
        "甲": "jia"
        # Neighbors intentionally missing.
    }

    monkeypatch.setattr(quiz_module, "load_confusion_map", lambda hsk_level: fake_confusion_map)
    monkeypatch.setattr(quiz_module, "CHAR_TO_PINYIN", fake_pinyin)
    monkeypatch.setattr(quiz_module.random, "sample", lambda population, k: list(population)[:k])
    monkeypatch.setattr(quiz_module.random, "shuffle", lambda options: None)

    response = client.get("/api/quiz/generate?difficulty=hard&count=1")

    assert response.status_code == 200
    question = response.json()["questions"][0]

    assert question["target"] == "甲"
    assert question["target_pinyin"] == "jia"

    neighbor_options = [
        option for option in question["options"]
        if option["is_correct"] is False
    ]

    assert neighbor_options[0]["pinyin"] == "乙"
    assert neighbor_options[1]["pinyin"] == "丙"
    assert neighbor_options[2]["pinyin"] == "丁"


def test_generate_quiz_hard_difficulty_uses_closest_neighbors(monkeypatch):
    """Hard difficulty should use neighbors starting from index 0."""
    quiz_module = get_quiz_module()

    fake_confusion_map = {
        "你": [
            ["他", 0.95],
            ["们", 0.90],
            ["好", 0.85],
            ["水", 0.80],
            ["火", 0.75],
            ["木", 0.70],
            ["山", 0.65],
        ]
    }

    fake_pinyin = {
        "你": "ni",
        "他": "ta",
        "们": "men",
        "好": "hao",
        "水": "shui",
        "火": "huo",
        "木": "mu",
        "山": "shan",
    }

    monkeypatch.setattr(quiz_module, "load_confusion_map", lambda hsk_level: fake_confusion_map)
    monkeypatch.setattr(quiz_module, "CHAR_TO_PINYIN", fake_pinyin)
    monkeypatch.setattr(quiz_module.random, "sample", lambda population, k: list(population)[:k])
    monkeypatch.setattr(quiz_module.random, "shuffle", lambda options: None)

    response = client.get("/api/quiz/generate?difficulty=hard&count=1")

    assert response.status_code == 200
    options = response.json()["questions"][0]["options"]

    distractor_characters = [
        option["character"] for option in options
        if option["is_correct"] is False
    ]

    assert distractor_characters == ["他", "们", "好"]


def test_generate_quiz_medium_difficulty_skips_first_two_neighbors(monkeypatch):
    """Medium difficulty should use neighbors starting from index 2."""
    quiz_module = get_quiz_module()

    fake_confusion_map = {
        "你": [
            ["他", 0.95],
            ["们", 0.90],
            ["好", 0.85],
            ["水", 0.80],
            ["火", 0.75],
            ["木", 0.70],
            ["山", 0.65],
        ]
    }

    fake_pinyin = {
        "你": "ni",
        "他": "ta",
        "们": "men",
        "好": "hao",
        "水": "shui",
        "火": "huo",
        "木": "mu",
        "山": "shan",
    }

    monkeypatch.setattr(quiz_module, "load_confusion_map", lambda hsk_level: fake_confusion_map)
    monkeypatch.setattr(quiz_module, "CHAR_TO_PINYIN", fake_pinyin)
    monkeypatch.setattr(quiz_module.random, "sample", lambda population, k: list(population)[:k])
    monkeypatch.setattr(quiz_module.random, "shuffle", lambda options: None)

    response = client.get("/api/quiz/generate?difficulty=medium&count=1")

    assert response.status_code == 200
    options = response.json()["questions"][0]["options"]

    distractor_characters = [
        option["character"] for option in options
        if option["is_correct"] is False
    ]

    assert distractor_characters == ["好", "水", "火"]


def test_generate_quiz_easy_difficulty_skips_first_four_neighbors(monkeypatch):
    """Easy difficulty should use neighbors starting from index 4."""
    quiz_module = get_quiz_module()

    fake_confusion_map = {
        "你": [
            ["他", 0.95],
            ["们", 0.90],
            ["好", 0.85],
            ["水", 0.80],
            ["火", 0.75],
            ["木", 0.70],
            ["山", 0.65],
        ]
    }

    fake_pinyin = {
        "你": "ni",
        "他": "ta",
        "们": "men",
        "好": "hao",
        "水": "shui",
        "火": "huo",
        "木": "mu",
        "山": "shan",
    }

    monkeypatch.setattr(quiz_module, "load_confusion_map", lambda hsk_level: fake_confusion_map)
    monkeypatch.setattr(quiz_module, "CHAR_TO_PINYIN", fake_pinyin)
    monkeypatch.setattr(quiz_module.random, "sample", lambda population, k: list(population)[:k])
    monkeypatch.setattr(quiz_module.random, "shuffle", lambda options: None)

    response = client.get("/api/quiz/generate?difficulty=easy&count=1")

    assert response.status_code == 200
    options = response.json()["questions"][0]["options"]

    distractor_characters = [
        option["character"] for option in options
        if option["is_correct"] is False
    ]

    assert distractor_characters == ["火", "木", "山"]