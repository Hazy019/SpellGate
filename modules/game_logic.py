import random
import json
import csv
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables (from gemini.env due to .env folder conflict)
load_dotenv("gemini.env")
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)

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

def calculate_level(mastered_words):
    """
    Calculates the player's level based on mastered words count.
    Returns (Level Name, Min Length, Max Length)
    """
    count = len(mastered_words)
    if count < 15:
        return "Novice", 3, 4
    elif count < 30:
        return "Apprentice", 5, 6
    else:
        return "Scholar", 7, 15  # 7+ letters

def fetch_gemini_words(level_name, min_len, max_len, count, excluded_words):
    """
    Calls Gemini API to generate words.
    Returns a list of words or an empty list on failure. 
    """
    if not api_key:
        print("Gemini API key not found in environment.")
        return []

    try:
        # Use full model path to avoid 404 on some API versions
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        system_instruction = (
            f"You are an offline spelling teacher. Output exactly {count} words. "
            "Do not use profanity. Do not output anything except a JSON array. "
            "Ensure the words are not in the excluded list provided."
        )
        
        user_prompt = (
            f"Generate words. The user is {level_name}, so generate words between {min_len} and {max_len} letters long. "
            f"Excluded words (do not generate these): {', '.join(excluded_words[:100])}"
        )

        response = model.generate_content(
            f"System: {system_instruction}\nUser: {user_prompt}",
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json",
            )
        )
        
        words = json.loads(response.text)
        if isinstance(words, list):
            # Cleanup: ensure caps and length constraints (AI can be creative)
            return [w.upper() for w in words if isinstance(w, str) and min_len <= len(w) <= max_len]
        return []

    except Exception as e:
        print(f"Gemini API Error: {e}")
        return []

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

    stats["attempts"] += 1 # Fixed: Increment attempts

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
    The 'Recruiter' logic: Fills the active list with 12 words.
    Priorities: Learning Pool > Gemini AI Words > Fallback CSV.
    """
    # 1. Start with what's already in the learning pool
    active_pool = list(progress_data.get("learning_pool", {}).keys())
    
    if len(active_pool) >= count:
        return active_pool[:count]

    # 2. Calculate requirements
    missing_count = count - len(active_pool)
    mastered = progress_data.get("mastered_words", [])
    level_name, min_l, max_l = calculate_level(mastered)
    
    # 3. Attempt Gemini fetch
    excluded = mastered + active_pool
    new_words = fetch_gemini_words(level_name, min_l, max_l, missing_count, excluded)
    
    # 4. Fallback logic if Gemini fails or returns insufficient results
    if len(new_words) < missing_count:
        print(f"Gemini provided {len(new_words)} words. Falling back to CSV for remaining.")
        try:
            with open(csv_path, mode='r') as file:
                reader = csv.reader(file)
                all_csv_words = [row[0].upper() for row in reader if row]
            
            # Filter CSV words by length and mastery
            suitable_csv = [
                w for w in all_csv_words 
                if min_l <= len(w) <= max_l 
                and w not in excluded 
                and w not in new_words
            ]
            random.shuffle(suitable_csv)
            new_words.extend(suitable_csv[:missing_count - len(new_words)])
            
        except Exception as e:
            print(f"Fallback CSV Error: {e}")

    # 5. Populate Learning Pool
    for word in new_words:
        if word not in progress_data["learning_pool"]:
            progress_data["learning_pool"][word] = {"correct_strikes": 0, "attempts": 0}
            active_pool.append(word)
        if len(active_pool) >= count:
            break

    return active_pool[:count]

def save_progress(progress_data, file_path = "data/user_progress.json"):
    """Saves the updated 'Report Card' to the JSON filing cabinet."""
    with open(file_path, 'w') as f:
        json.dump(progress_data, f, indent = 4)

    

