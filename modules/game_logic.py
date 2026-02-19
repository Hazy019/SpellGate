import random

def generate_scrambled(word):
    """Replace middle characters with underscores(e.g., 'Apple' -> 'A_p_e')"""
    if len(word) < 3:
        return f"{word[0]}_"
    
    chars = list(word)

    for i in range(1, len(chars) - 1):
        if random.random() > 0.5:
            chars[i] = "_"
    return "".join(chars)

def update_mastery(word, is_correct, progress_data):
    """Update the JSON logic for word proficiency"""
    stats = progress_data["learning_pool"].get(word, {"correct_strikes": 0})

    if is_correct:
        stats["correct_strikes"] += 1
    else:
        stats["correct_strikes"] = 0

    if stats["correct_strikes"] >= 3:
        progress_data["mastered_words"].append(word)