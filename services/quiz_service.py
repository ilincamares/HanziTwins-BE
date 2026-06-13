import random

from services.utils import get_confusion_map, get_char_to_pinyin_map


class QuizService:
    def generate_quiz(
            self,
            hsk_level: str,
            count: int,
            difficulty: str,
    ):
        if hsk_level.lower() != "all":
            if not hsk_level.isdigit():
                raise ValueError("HSK level must be number.")
            if int(hsk_level) < 1 or int(hsk_level) > 6:
                raise ValueError("HSK level must be between 1 and 6.")

        if count < 1:
            raise ValueError(f"Number of questions to generate must be greater than 0.")

        if difficulty.lower() not in ["easy", "medium", "hard"]:
            raise ValueError(f"Difficulty {difficulty} is not supported.")

        confusion_map = get_confusion_map(hsk_level)

        available_characters = list(confusion_map.keys())

        actual_count = min(count, len(available_characters))

        selected_targets = random.sample(available_characters, actual_count)

        quiz_questions = []

        for target in selected_targets:
            neighbors_data = confusion_map.get(target, [])
            pinyin_map = get_char_to_pinyin_map()
            target_pinyin = pinyin_map.get(target, target)

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
            else:
                start_idx = 4

            distractors_found = 0
            for neighbour_char, score in neighbors_data[start_idx:]:
                neighbour_pinyin = pinyin_map.get(neighbour_char, neighbour_char)

                if neighbour_pinyin not in seen_pinyins:
                    options_rich.append({
                        "character": neighbour_char,
                        "pinyin": neighbour_pinyin,
                        "similarity": score,
                        "is_correct": False
                    })
                    seen_pinyins.add(neighbour_pinyin)
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