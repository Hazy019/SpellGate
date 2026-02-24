import random
import json
import csv
import os

def generate_scrambled(word):
    """Replace middle characters with underscores(e.g., 'Apple' -> 'A_p_e')"""
    if len(word) < 3:
        return f"{word[0]}_"
    
    chars = list(word)

    for i in range(1, len(chars) - 1):
        if random.random() > 0.4:
            chars[i] = "_"
    return "".join(chars)

def update_mastery(word, is_correct, hint_used, progress_data):
    """Update the JSON logic for word proficiency"""
    if word not in progress_data["learning_pool"]:
        progress_data["learning_pool"][word] = {"correct_strike": 0, "attempts": 0}

    stats = progress_data["learning_pool"][word]
    stats["attempts"] += 1

    if is_correct and not hint_used:
        stats["correct_strikes"] += 1
    else:
        stats["correct_strikes"] = 0

    if stats["correct_strikes"] >= 3:
        if word not in progress_data["mastered_words"]:
            progress_data["mastered_words"].append(word)
        del progress_data["learning_pool"][word]
        return True

    return False

def get_next_words(progress_data, csv_path, count=12):
    """
    The 'Recruiter' logic: Fills the active list with 12 word.
    Priorities: Learning Pool > New Words from CSV.
    """
    active_pool = list(progress_data["learning_pool"].keys())

    if len(active_pool) < count:
        try:
            with open(csv_path, mode='r') as file:
                reader = csv.reader(file)
                all_csv_words = [row[0].upper() for row in reader if row]

            for word in all_csv_words:
                if (word not in progress_data["mastered_words"] and
                    word not in progress_data["learning_pool"]):

                    progress_data["learning_pool"][word] = {"correct_strikes": 0, "attempts": 0}
                    active_pool.append(word)

                if len(active_pool) >= count:
                    break
        
        except FileNotFoundError:
            print("Error: word.csv not found. Please create it in assists/folder.")
        
    return active_pool[:count]

def save_progress(progress_data, file_path = "data/user_progress.json"):
    """Saves the updated 'Report Card' to the JSON filing cabinet."""
    with open(file_path, 'w') as f:
        json.dump(progress_data, f, indent = 4)

    

