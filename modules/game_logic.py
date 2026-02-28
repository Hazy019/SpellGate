import random
import json
import csv

def generate_scrambled(word):
    """Replace middle characters with underscores(e.g., 'Apple' -> 'A_p_e')"""
    n = len(word)
    
    if n <= 2:
        return word

    if n == 3:
        num_to_hide = 1
    elif n == 4:
        num_to_hide = 2
    elif n == 5:
        num_to_hide = random.choice([2, 3])
    else:
        num_to_hide = random.randint(3, max(3, n // 2))

    chars = list(word)
    
    available_indices = list(range(1, n - 1))
    
    num_to_hide = min(num_to_hide, len(available_indices))
    indices_to_hide = random.sample(available_indices, num_to_hide)
    
    for idx in indices_to_hide:
        chars[idx] = "_"
        
    return "".join(chars)

def update_mastery(word, is_correct, hint_used, progress_data):
    """Update the JSON logic for word proficiency"""
    if "learning_pool" not in progress_data:
        progress_data["learning_pool"] = {}
    
    if word not in progress_data["learning_pool"] or not isinstance(progress_data["learning_pool"][word],dict):
        progress_data["learning_pool"][word] = {"correct_strikes": 0, "attempts": 0}

    stats = progress_data["learning_pool"][word]

    if "correct_strikes" not in stats:
        stats["correct_strikes"] = 0 
    if "attempts" not in stats: 
        stats["attempts"] = 0

    stats["attempts"] = 0

    if is_correct and not hint_used:
        stats["correct_strikes"] += 1
    else:
        stats["correct_strikes"] = 0

    if stats["correct_strikes"] >= 3:
        if "mastered_words" not in progress_data:
            progress_data["mastered_words"] = []

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
            print("Error: word.csv not found.")
        
    return active_pool[:count]

def save_progress(progress_data, file_path = "data/user_progress.json"):
    """Saves the updated 'Report Card' to the JSON filing cabinet."""
    with open(file_path, 'w') as f:
        json.dump(progress_data, f, indent = 4)

    

