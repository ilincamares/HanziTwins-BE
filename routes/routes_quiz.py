import json
import os
import random

import pandas
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCEL_PATH = os.path.join(BASE_DIR, "assets", "General_Standard_Hanzi.xlsx")

print("Loading Pinyin dictionary into memory...")
try:
    df = pandas.read_excel(EXCEL_PATH)

    df = df.dropna(subset=['Pinyin'])

    CHAR_TO_PINYIN = df.set_index('Character')['Pinyin'].to_dict()
except Exception as e:
    print(f"Error loading Excel file: {e}")
    CHAR_TO_PINYIN = {}



def load_confusion_map(hsk_level: str):
    if hsk_level.lower() == "all":
        filename = "confusion_map_full.json"
    else:
        filename = "confusion_map_hsk_{}.json".format(hsk_level.lower())

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, "assets", "confusion_maps", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail=f"Data for character set not found.")

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@router.get("/generate")
def generate_quiz(
        hsk_level: str = Query("all", description="HSK level (1-6) or 'all'"),
        count: int = Query(5, description="Number of questions to generate."),
        difficulty: str = Query("medium", description="Difficulty: easy, medium, hard"),
):
    if hsk_level.lower() != "all":
        if not hsk_level.isdigit():
            raise HTTPException(status_code=400, detail=f"HSK level {hsk_level} must be number.")
        if int(hsk_level) < 1 or int(hsk_level) > 6:
            raise HTTPException(status_code=400, detail=f"HSK level {hsk_level} must be between 1 and 6.")

    if count < 1:
        raise HTTPException(status_code=400, detail=f"Number of questions to generate must be greater than 0.")

    if difficulty.lower() not in ["easy", "medium", "hard"]:
        raise HTTPException(status_code=400, detail=f"Difficulty {difficulty} is not supported.")

    confusion_map = load_confusion_map(hsk_level)

    available_characters = list(confusion_map.keys())

    actual_count = min(count, len(available_characters))

    selected_targets = random.sample(available_characters, actual_count)

    quiz_questions = []

    for target in selected_targets:
        neighbors_data = confusion_map.get(target, [])
        target_pinyin = CHAR_TO_PINYIN.get(target, target)

        options_rich = [{
            "character": target,
            "pinyin": target_pinyin,
            "similarity": 100.0,
            "is_correct": True
        }]

        seen_pinyins = {target_pinyin}

        difficulty = difficulty.lower()

        if difficulty == "hard":
            start_idx = 0
        elif difficulty == "medium":
            start_idx = 2
        else:  # easy
            start_idx = 4

        distractors_found = 0
        for rh_char, score in neighbors_data[start_idx:]:
            rh_pinyin = CHAR_TO_PINYIN.get(rh_char, rh_char)

            if rh_pinyin not in seen_pinyins:
                options_rich.append({
                    "character": rh_char,
                    "pinyin": rh_pinyin,
                    "similarity": score,
                    "is_correct": False
                })
                seen_pinyins.add(rh_pinyin)
                distractors_found += 1

            if distractors_found == 3:
                break

        random.shuffle(options_rich)

        quiz_questions.append({
            "target": target,
            "target_pinyin": target_pinyin,
            "options": options_rich
        })

    return {
        "metadata": {
            "hsk_level": hsk_level,
            "difficulty": difficulty,
            "questions_count": actual_count,
        },
        "questions": quiz_questions
    }