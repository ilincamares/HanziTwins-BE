import pytest

import services.quiz_service as quiz_module
from services.quiz_service import QuizService


FAKE_CONFUSION_MAP = {
    "你": [
        ["他", 0.95],
        ["们", 0.90],
        ["好", 0.85],
        ["水", 0.80],
        ["火", 0.75],
        ["木", 0.70],
        ["山", 0.65],
    ],
    "好": [
        ["你", 0.95],
        ["他", 0.90],
        ["们", 0.85],
        ["水", 0.80],
    ],
}

FAKE_PINYIN = {
    "你": "nǐ",
    "他": "tā",
    "们": "men",
    "好": "hǎo",
    "水": "shuǐ",
    "火": "huǒ",
    "木": "mù",
    "山": "shān",
}


@pytest.fixture(autouse=True)
def patch_quiz_assets(monkeypatch):
    monkeypatch.setattr(
        quiz_module,
        "get_confusion_map",
        lambda hsk_level: FAKE_CONFUSION_MAP,
    )

    monkeypatch.setattr(
        quiz_module,
        "get_char_to_pinyin_map",
        lambda: FAKE_PINYIN,
    )

    monkeypatch.setattr(
        quiz_module.random,
        "sample",
        lambda population, k: list(population)[:k],
    )

    monkeypatch.setattr(
        quiz_module.random,
        "shuffle",
        lambda options: None,
    )


def test_generate_quiz_returns_expected_structure():
    service = QuizService()

    result = service.generate_quiz(
        hsk_level="all",
        count=1,
        difficulty="hard",
    )

    assert result["metadata"]["hsk_level"] == "all"
    assert result["metadata"]["difficulty"] == "hard"
    assert result["metadata"]["questions_count"] == 1

    question = result["questions"][0]

    assert question["target"] == "你"
    assert question["target_pinyin"] == "nǐ"
    assert "options" in question


def test_generate_quiz_has_exactly_one_correct_answer():
    service = QuizService()

    result = service.generate_quiz(
        hsk_level="all",
        count=1,
        difficulty="hard",
    )

    options = result["questions"][0]["options"]

    correct_options = [
        option for option in options
        if option["is_correct"] is True
    ]

    assert len(correct_options) == 1
    assert correct_options[0]["character"] == "你"
    assert correct_options[0]["pinyin"] == "nǐ"
    assert correct_options[0]["similarity"] == 100.0


def test_generate_quiz_hard_uses_closest_neighbors():
    service = QuizService()

    result = service.generate_quiz(
        hsk_level="all",
        count=1,
        difficulty="hard",
    )

    distractors = [
        option["character"]
        for option in result["questions"][0]["options"]
        if option["is_correct"] is False
    ]

    assert distractors == ["他", "们", "好"]


def test_generate_quiz_medium_skips_first_two_neighbors():
    service = QuizService()

    result = service.generate_quiz(
        hsk_level="all",
        count=1,
        difficulty="medium",
    )

    distractors = [
        option["character"]
        for option in result["questions"][0]["options"]
        if option["is_correct"] is False
    ]

    assert distractors == ["好", "水", "火"]


def test_generate_quiz_easy_skips_first_four_neighbors():
    service = QuizService()

    result = service.generate_quiz(
        hsk_level="all",
        count=1,
        difficulty="easy",
    )

    distractors = [
        option["character"]
        for option in result["questions"][0]["options"]
        if option["is_correct"] is False
    ]

    assert distractors == ["火", "木", "山"]


def test_generate_quiz_rejects_invalid_difficulty():
    service = QuizService()

    with pytest.raises(ValueError, match="not supported"):
        service.generate_quiz(
            hsk_level="all",
            count=1,
            difficulty="expert",
        )


def test_generate_quiz_rejects_invalid_hsk_level():
    service = QuizService()

    with pytest.raises(ValueError, match="between 1 and 6"):
        service.generate_quiz(
            hsk_level="7",
            count=1,
            difficulty="medium",
        )


def test_generate_quiz_rejects_non_numeric_hsk_level():
    service = QuizService()

    with pytest.raises(ValueError, match="must be number"):
        service.generate_quiz(
            hsk_level="abc",
            count=1,
            difficulty="medium",
        )


def test_generate_quiz_rejects_zero_count():
    service = QuizService()

    with pytest.raises(ValueError, match="greater than 0"):
        service.generate_quiz(
            hsk_level="all",
            count=0,
            difficulty="medium",
        )


def test_generate_quiz_skips_duplicate_pinyin(monkeypatch):
    duplicate_map = {
        "甲": [
            ["乙", 0.95],
            ["丙", 0.90],
            ["丁", 0.85],
            ["戊", 0.80],
        ]
    }

    duplicate_pinyin = {
        "甲": "a",
        "乙": "a",
        "丙": "b",
        "丁": "c",
        "戊": "d",
    }

    monkeypatch.setattr(
        quiz_module,
        "get_confusion_map",
        lambda hsk_level: duplicate_map,
    )

    monkeypatch.setattr(
        quiz_module,
        "get_char_to_pinyin_map",
        lambda: duplicate_pinyin,
    )

    service = QuizService()

    result = service.generate_quiz(
        hsk_level="all",
        count=1,
        difficulty="hard",
    )

    pinyins = [
        option["pinyin"]
        for option in result["questions"][0]["options"]
    ]

    assert pinyins == ["a", "b", "c", "d"]
    assert len(pinyins) == len(set(pinyins))