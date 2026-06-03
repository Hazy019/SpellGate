import random
import json
import csv
import os
from dotenv import load_dotenv
from modules.config import USER_PROGRESS_FILE, TIME_BANK_FILE

# ─────────────────────────────────────────────────────────────
#  ENVIRONMENT SETUP
# ─────────────────────────────────────────────────────────────
load_dotenv("gemini.env")
api_key = os.getenv("GEMINI_API_KEY")

# ─────────────────────────────────────────────────────────────
#  3-MODEL FALLBACK CHAIN  (what you call a "Model Cascade")
#  If Model 1 fails → try Model 2 → try Model 3 → go Offline
# ─────────────────────────────────────────────────────────────
MODEL_CASCADE = [
    "gemini-2.0-flash",       # ① Primary  — fastest, smartest
    "gemini-1.5-flash",       # ② Fallback — stable, well-supported
    "gemini-2.0-flash-lite",  # ③ Last resort — lightest, most available
]

# ─────────────────────────────────────────────────────────────
#  OFFLINE WORD BANK  — used when ALL models are unreachable
#  Words are pre-grouped by tier so the difficulty system still
#  works 100% without internet.
# ─────────────────────────────────────────────────────────────
OFFLINE_WORD_BANK = {
    "Novice": [  # 3–4 letters
        ("CAT", "The cat sat on a warm mat."),
        ("DOG", "A dog can wag its tail fast."),
        ("RUN", "She can run very fast in the park."),
        ("SUN", "The sun shines bright every day."),
        ("MAP", "We used a map to find the park."),
        ("FLY", "Birds can fly high in the sky."),
        ("CUP", "Fill the cup with cold water."),
        ("HOP", "The frog can hop over the log."),
        ("JAM", "Spread the jam on your bread."),
        ("KIT", "The first-aid kit has bandages."),
        ("LOG", "The log floated down the river."),
        ("MOP", "Use the mop to clean the floor."),
        ("NET", "The butterfly flew into the net."),
        ("OAK", "The oak tree is very old and tall."),
        ("PAN", "Fry the egg in the pan."),
        ("RAG", "Wipe the spill with an old rag."),
        ("SAP", "The sap from the tree is sticky."),
        ("TUB", "Fill the tub with warm water."),
        ("VAN", "We moved boxes in a big van."),
        ("WAX", "Polish the car with wax."),
        ("YAM", "Yam is a tasty orange vegetable."),
        ("ZAP", "The lightning can zap a tree."),
        ("APE", "The ape swings from branch to branch."),
        ("BEE", "A bee makes sweet honey."),
        ("COW", "The cow gives us milk."),
        ("DEN", "The fox hid in its den."),
        ("EGG", "Crack the egg into the bowl."),
        ("FAN", "The fan cools the hot room."),
        ("GEM", "The gem sparkled in the sunlight."),
        ("HEN", "The hen laid three eggs today."),
        ("INK", "The pen ran out of ink."),
        ("JOG", "I jog every morning to stay fit."),
        ("KEY", "Use the key to open the door."),
        ("LID", "Put the lid on the pot."),
        ("MUD", "The puppy splashed in the mud."),
        ("NUT", "A squirrel stores nuts for winter."),
        ("OWL", "The owl hoots at night."),
        ("POD", "Peas grow inside a green pod."),
        ("ROD", "The fishing rod bent when the fish pulled."),
        ("SKY", "The sky is blue and clear today."),
        ("TIN", "Store cookies in a tin box."),
        ("URN", "The flowers sat in a clay urn."),
        ("VET", "The vet helped the sick puppy."),
        ("WIG", "She wore a curly red wig."),
        ("YEW", "The yew tree is ever green."),
        ("ZEN", "He felt calm and zen after resting."),
        ("BIRD", "The bird sang a sweet morning song."),
        ("FISH", "The fish swam deep in the lake."),
        ("TREE", "The tree lost its leaves in fall."),
        ("STAR", "Each star in the sky is a sun."),
        ("MOON", "The moon lights the night sky."),
        ("FIRE", "Do not play near an open fire."),
        ("SNOW", "Children love to play in the snow."),
        ("WIND", "The wind blew the kite up high."),
        ("RAIN", "Rain helps flowers and trees grow."),
        ("BOOK", "Read a book to learn something new."),
        ("GOLD", "Miners searched the river for gold."),
        ("LEAF", "Each leaf turns red in autumn."),
        ("FROG", "The green frog jumped into the pond."),
        ("LION", "The lion is the king of the jungle."),
        ("BEAR", "A bear hibernates through winter."),
        ("WOLF", "The wolf howled at the full moon."),
        ("HAWK", "The hawk soared high above the field."),
        ("CAKE", "We baked a chocolate cake for the party."),
        ("DARK", "Turn on the light — it is too dark."),
        ("EARN", "Study hard and you will earn good grades."),
        ("FARM", "Chickens and cows live on the farm."),
        ("GATE", "Close the gate so the dog cannot escape."),
        ("HIVE", "Bees live and make honey in a hive."),
        ("IRON", "Iron is a strong and heavy metal."),
        ("JUMP", "Can you jump over the puddle?"),
        ("KITE", "She flew a red kite on a windy day."),
        ("LAMP", "Switch on the lamp — it is getting dark."),
        ("MIST", "The morning mist covered the valley."),
        ("NEST", "The robin built a cozy nest."),
        ("OPEN", "Please open the window for fresh air."),
        ("PARK", "We played soccer at the park."),
        ("QUIZ", "The spelling quiz was fun and fair."),
        ("REEF", "Colorful fish live on the coral reef."),
        ("SEED", "Plant a seed and watch it grow."),
        ("TIDE", "The tide washed shells onto the beach."),
        ("USED", "The library sells used books cheaply."),
        ("VINE", "The vine climbed the old stone wall."),
        ("WORM", "Birds eat worms early in the morning."),
        ("XRAY", "The doctor used an X-ray to check the bone."),
        ("YARD", "Children played games in the yard."),
        ("ZERO", "The scoreboard showed zero at the start."),
    ],
    "Apprentice": [  # 5–6 letters
        ("APPLE", "The apple fell from the tree."),
        ("BRAVE", "It is brave to try something new."),
        ("CLIMB", "We will climb the tall oak tree."),
        ("DREAM", "Follow your dream and never give up."),
        ("EARTH", "Earth is the third planet from the sun."),
        ("FLAME", "The candle flame flickered in the breeze."),
        ("GRACE", "The dancer moved with great grace."),
        ("HEART", "Exercise keeps your heart strong."),
        ("IMAGE", "Draw an image of your favorite animal."),
        ("JEWEL", "The crown was covered in bright jewels."),
        ("KNEEL", "Kneel down to look at the small flower."),
        ("LIGHT", "Light travels faster than sound."),
        ("MAGIC", "Reading feels like magic for the mind."),
        ("NIGHT", "Owls are active during the night."),
        ("OCEAN", "The ocean is deeper than the tallest mountain."),
        ("PIANO", "She practices piano every afternoon."),
        ("QUEEN", "The queen waved to the crowd from the balcony."),
        ("RIVER", "The river flows gently to the sea."),
        ("SCOUT", "The scout helped elderly people cross the street."),
        ("TIGER", "The tiger has orange and black stripes."),
        ("UNCLE", "My uncle taught me how to fish."),
        ("VENOM", "Some snakes carry dangerous venom."),
        ("WATER", "Drink plenty of water every day."),
        ("XENON", "Xenon is a gas used in bright lamps."),
        ("YOUNG", "Young trees need water and sunlight to grow."),
        ("ZEBRA", "A zebra has black and white stripes."),
        ("ACORN", "Squirrels bury acorns for winter food."),
        ("BLEND", "Blend the fruits to make a smoothie."),
        ("CLOUD", "A fluffy cloud drifted across the sky."),
        ("DEPOT", "The train arrived at the central depot."),
        ("ELBOW", "She bumped her elbow on the table."),
        ("FLINT", "Flint was used to make fire long ago."),
        ("GLOBE", "Spin the globe to find any country."),
        ("HOVER", "The helicopter could hover over the field."),
        ("IVORY", "Elephants have beautiful ivory tusks."),
        ("JOUST", "Knights would joust in tournaments."),
        ("KNACK", "She has a knack for solving puzzles."),
        ("LEMON", "Lemon juice makes water taste refreshing."),
        ("MAPLE", "Maple trees give us sweet syrup."),
        ("NOVEL", "I finished reading the novel in one day."),
        ("OLIVE", "Olives grow on trees in sunny places."),
        ("POLAR", "Polar bears live in the Arctic."),
        ("QUEST", "The hero went on a quest for the lost treasure."),
        ("REALM", "The dragon ruled over the magical realm."),
        ("STORM", "The storm knocked down two big trees."),
        ("TORCH", "The guide carried a torch into the cave."),
        ("ULTRA", "The runner set an ultra-fast record."),
        ("VIOLA", "She plays the viola in the school orchestra."),
        ("WHEAT", "Bread is made from ground wheat."),
        ("XYLEM", "Xylem carries water up through a plant."),
        ("YACHT", "The yacht sailed across the calm bay."),
        ("ZONAL", "The zonal map showed different climate areas."),
        ("ABOVE", "The bird flew above the tall building."),
        ("BIRDS", "Many birds migrate south each winter."),
        ("CRISP", "The autumn air felt crisp and fresh."),
        ("DUSTY", "The old library shelf was very dusty."),
        ("EQUAL", "Everyone deserves an equal chance."),
        ("FROST", "Frost covered the grass on winter mornings."),
        ("GRAND", "The waterfall was truly grand and powerful."),
        ("HERBS", "Herbs like basil add flavor to food."),
        ("INDEX", "Use the index to find the page quickly."),
        ("JOKER", "The joker card can replace any card in the game."),
        ("KNOBS", "Turn the knobs to adjust the volume."),
        ("LUNAR", "A lunar eclipse happens when Earth blocks the sun."),
        ("MINOR", "The minor key makes music sound sad."),
        ("NORTH", "A compass always points to the north."),
        ("ORBIT", "The moon is in orbit around the Earth."),
        ("PLANT", "Water your plant every three days."),
        ("QUIET", "The library must stay quiet for readers."),
        ("RALLY", "The team held a rally before the big game."),
        ("SMART", "Working smart is as important as working hard."),
        ("TRAIL", "We hiked the forest trail for two hours."),
        ("UNITY", "Unity makes a team stronger."),
        ("VAPOR", "Water vapor rises from a hot cup of tea."),
        ("WITCH", "The witch in the story had a magic broom."),
        ("XEROX", "Please xerox that document for the class."),
        ("YEAST", "Yeast makes bread dough rise and puff up."),
        ("ZONES", "The city has quiet zones near the hospital."),
    ],
    "Scholar": [  # 7–15 letters
        ("CAPTAIN", "The captain guided the ship through the storm."),
        ("DESTINY", "Hard work shapes your own destiny."),
        ("EXPLORE", "Scientists explore the ocean floor."),
        ("FORWARD", "Always look forward and keep improving."),
        ("GRAVITY", "Gravity keeps planets in orbit."),
        ("HISTORY", "History teaches us about the past."),
        ("INSPIRE", "Great teachers inspire their students."),
        ("JOURNEY", "Every long journey begins with one step."),
        ("KINGDOM", "The kingdom was known for its kindness."),
        ("LANTERN", "The lantern lit the dark forest path."),
        ("MACHINE", "The machine sorted letters at high speed."),
        ("NETWORK", "The internet is a global network."),
        ("OPINION", "Everyone has a right to their own opinion."),
        ("PATTERN", "The pattern on the butterfly wing was unique."),
        ("QUARTER", "A quarter is equal to twenty-five cents."),
        ("RESTORE", "Workers helped restore the old painting."),
        ("SILENCE", "Silence filled the room during the test."),
        ("THUNDER", "Thunder roared across the dark sky."),
        ("UNIFORM", "All students wore a neat uniform to school."),
        ("VIBRANT", "The market was vibrant with color and sound."),
        ("WARRIOR", "A warrior fights with courage and skill."),
        ("XYLOPHONE", "She tapped each key of the xylophone gently."),
        ("YEARNING", "She felt a yearning to travel the world."),
        ("ZOOLOGY", "Zoology is the study of animal life."),
        ("ABSOLUTE", "The answer was absolute — there was no doubt."),
        ("BASEBALL", "Baseball is a popular sport in the spring."),
        ("CALENDAR", "Mark the date on the calendar."),
        ("DIAMETER", "The diameter of the circle was ten centimeters."),
        ("ELEPHANT", "An elephant uses its trunk to drink water."),
        ("FRAGMENT", "A fragment of the meteor landed in a field."),
        ("GRATEFUL", "I am grateful for your help today."),
        ("HERITAGE", "Music is an important part of our heritage."),
        ("INNOCENT", "The puppy looked innocent after chewing the sock."),
        ("JEALOUSY", "Jealousy can hurt friendships."),
        ("KEYBOARD", "Type your answer on the keyboard."),
        ("LANDMARK", "The old lighthouse is a famous landmark."),
        ("MONUMENT", "The monument honors brave firefighters."),
        ("NAVIGATE", "Sailors use stars to navigate at sea."),
        ("OBSTACLE", "An obstacle can make you stronger."),
        ("PARADISE", "The tropical island felt like paradise."),
        ("QUANTITY", "A large quantity of rain fell overnight."),
        ("RATIONAL", "Make a rational decision based on facts."),
        ("SENTENCE", "Write a sentence using your spelling word."),
        ("THOUSAND", "A thousand seconds is about seventeen minutes."),
        ("UNIVERSE", "Our universe contains billions of galaxies."),
        ("VARIABLE", "A variable in math represents an unknown number."),
        ("WHATEVER", "Whatever you choose, give it your best effort."),
        ("XYLOCARB", "Scientists study xylocarb compounds in wood."),
        ("YESTERDAY", "Yesterday I finished my science project."),
        ("ZEPPELIN", "A zeppelin is a large airship filled with gas."),
        ("BEAUTIFUL", "The rainbow was absolutely beautiful."),
        ("CALCULATE", "You can calculate the answer step by step."),
        ("DEMOCRACY", "Democracy gives citizens the right to vote."),
        ("EDUCATION", "Education is the key to opportunity."),
        ("FREQUENCY", "The frequency of the alarm was very loud."),
        ("GEOGRAPHY", "Geography helps us understand where places are."),
        ("HIBERNATE", "Bears hibernate through the cold winter."),
        ("IMAGINARY", "The unicorn is an imaginary creature."),
        ("KNOWLEDGE", "Knowledge grows the more you share it."),
        ("LONGITUDE", "Longitude measures how far east or west you are."),
        ("MEMORABLE", "Winning the spelling bee was truly memorable."),
        ("NECESSARY", "It is necessary to drink water every day."),
        ("OBVIOUSLY", "The answer was obviously correct."),
        ("PERMANENT", "A permanent marker does not wash off."),
        ("RESILIENT", "A resilient person bounces back from failure."),
        ("SECRETARY", "The school secretary organized all the records."),
        ("TELESCOPE", "Use a telescope to see distant stars."),
        ("VOLUNTEER", "A volunteer helps others without being paid."),
        ("WONDERFUL", "The science fair project was truly wonderful."),
        ("YESTERDAY", "Yesterday was the last day of the school term."),
        ("ACCOMPLISHMENT", "Finishing the book was a great accomplishment."),
        ("BREATHTAKING", "The mountain view was breathtaking."),
        ("CHAMPIONSHIP", "Our team won the regional championship."),
        ("DETERMINATION", "Her determination helped her win the race."),
        ("EXTRAORDINARY", "The magician performed extraordinary tricks."),
        ("IMAGINATION", "Imagination is the beginning of creation."),
    ],
}


# ─────────────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────────────

def generate_scrambled(word):
    """Replace middle characters with underscores (e.g., 'Apple' -> 'A_p_e')"""
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
    Calculates the player's level based on mastered word count.
    Returns (level_name, min_len, max_len)
    """
    count = len(mastered_words)
    if count < 15:
        return "Novice", 3, 4
    elif count < 30:
        return "Apprentice", 5, 6
    else:
        return "Scholar", 7, 15


# ─────────────────────────────────────────────────────────────
#  OFFLINE FALLBACK — always available, no internet needed
# ─────────────────────────────────────────────────────────────

def _offline_word_bank(level_name, min_len, max_len, count, excluded_words):
    """
    Returns words from the built-in offline bank, filtered by tier + exclusions.
    This is the final safety net — works 100% without internet.
    """
    pool = OFFLINE_WORD_BANK.get(level_name, OFFLINE_WORD_BANK["Novice"])
    excluded_upper = {w.upper() for w in excluded_words}

    candidates = [
        {"word": w.upper(), "sentence": s}
        for w, s in pool
        if min_len <= len(w) <= max_len and w.upper() not in excluded_upper
    ]
    random.shuffle(candidates)
    print(f"[Offline Bank] Returning {min(count, len(candidates))} words for tier '{level_name}'")
    return candidates[:count]



# ─────────────────────────────────────────────────────────────
#  SINGLE MODEL ATTEMPT
# ─────────────────────────────────────────────────────────────

def _try_model(model_name, level_name, min_len, max_len, count, excluded_words):
    """
    Tries a single Gemini model. Returns list of word dicts or raises on failure.
    Uses the new google-genai SDK.
    """
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)

    system_instruction = (
        f"You are an offline spelling teacher. Output exactly {count} words. "
        "Do not use profanity. Do not output anything except a JSON array of objects. "
        "Each object must have two keys: 'word' and 'sentence'. "
        "The 'sentence' should be short, educational, and fun for a 4th grader. "
        "Ensure the words are not in the excluded list provided."
    )

    user_prompt = (
        f"Generate words. The user is at '{level_name}' level, "
        f"so generate words between {min_len} and {max_len} letters long. "
        f"Excluded words (do not generate these): {', '.join(list(excluded_words)[:80])}"
    )

    response = client.models.generate_content(
        model=model_name,
        contents=f"System: {system_instruction}\nUser: {user_prompt}",
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    data = json.loads(response.text)
    if not isinstance(data, list):
        return []

    results = []
    for item in data:
        word = item.get("word", "").upper().strip()
        sentence = item.get("sentence", f"Can you spell {word}?")
        if min_len <= len(word) <= max_len:
            results.append({"word": word, "sentence": sentence})

    return results


# ─────────────────────────────────────────────────────────────
#  3-MODEL FALLBACK CHAIN  ← this is the cascade
# ─────────────────────────────────────────────────────────────

def _classify_error(e):
    """Returns a short ASCII-safe label for the error type."""
    msg = str(e)
    if "429" in msg or "RESOURCE_EXHAUSTED" in msg or "quota" in msg.lower():
        return "QUOTA_EXCEEDED (free tier limit hit)"
    if "403" in msg or "API_KEY" in msg or "PERMISSION" in msg:
        return "AUTH_ERROR (bad or missing key)"
    if "404" in msg or "not found" in msg.lower():
        return "MODEL_NOT_FOUND"
    if isinstance(e, (ConnectionError, TimeoutError, OSError)):
        return "NETWORK_ERROR (offline?)"
    return type(e).__name__


def fetch_gemini_words(level_name, min_len, max_len, count, excluded_words):
    """
    Fallback Chain (Model Cascade):
      [1] gemini-2.0-flash     -- fastest, smartest
      [2] gemini-1.5-flash     -- stable fallback
      [3] gemini-2.0-flash-lite -- lightest, most available
      [4] Offline word bank    -- no internet needed, always works
    """
    if not api_key:
        print("[Cascade] No API key -- going straight to offline bank.")
        return _offline_word_bank(level_name, min_len, max_len, count, excluded_words)

    for idx, model_name in enumerate(MODEL_CASCADE, start=1):
        try:
            print(f"[Cascade] [{idx}/{len(MODEL_CASCADE)}] Trying: {model_name}")
            results = _try_model(model_name, level_name, min_len, max_len, count, excluded_words)
            if results:
                print(f"[Cascade] OK  {model_name} returned {len(results)} words.")
                return results
            else:
                print(f"[Cascade] SKIP {model_name} returned empty list -- trying next.")
        except Exception as e:
            label = _classify_error(e)
            print(f"[Cascade] FAIL [{label}] {model_name} -- trying next model.")
            continue  # --> try the next model in the chain

    # All 3 models exhausted --> go fully offline
    print("[Cascade] All API models failed. Switching to offline word bank.")
    return _offline_word_bank(level_name, min_len, max_len, count, excluded_words)


# ─────────────────────────────────────────────────────────────
#  MASTERY LOGIC
# ─────────────────────────────────────────────────────────────

def update_mastery(word, is_correct, hint_used, progress_data):
    """
    Update the JSON mastery logic for a word.
    Returns True if the word just became mastered.
    """
    if "learning_pool" not in progress_data:
        progress_data["learning_pool"] = {}

    if word not in progress_data["learning_pool"] or not isinstance(progress_data["learning_pool"][word], dict):
        progress_data["learning_pool"][word] = {"correct_strikes": 0, "attempts": 0}

    stats = progress_data["learning_pool"][word]
    stats.setdefault("correct_strikes", 0)
    stats.setdefault("attempts", 0)

    stats["attempts"] += 1

    if is_correct and not hint_used:
        stats["correct_strikes"] += 1
    else:
        stats["correct_strikes"] = 0

    if stats["correct_strikes"] >= 3:
        progress_data.setdefault("mastered_words", [])
        if word not in progress_data["mastered_words"]:
            progress_data["mastered_words"].append(word)

        # Update level in JSON to stay in sync
        level_name, _, _ = calculate_level(progress_data["mastered_words"])
        progress_data["current_level"] = level_name

        del progress_data["learning_pool"][word]
        return True  # word mastered!

    return False


# ─────────────────────────────────────────────────────────────
#  WORD RECRUITER
# ─────────────────────────────────────────────────────────────

def get_next_words(progress_data, csv_path, count=12):
    """
    The 'Recruiter': fills the active word list with `count` words.
    Priority: Learning Pool > Fallback Chain (API → Offline Bank) > CSV.
    """
    # 1. Start with words already in the learning pool
    active_words = list(progress_data.get("learning_pool", {}).keys())

    if len(active_words) >= count:
        return [
            {"word": w, "sentence": progress_data["learning_pool"][w].get("sentence", f"Spell {w}.")}
            for w in active_words[:count]
        ]

    # 2. Determine how many new words we need
    missing_count = count - len(active_words)
    mastered = progress_data.get("mastered_words", [])
    level_name, min_l, max_l = calculate_level(mastered)
    excluded = set(mastered + active_words)

    # 3. Run the fallback chain (API → Offline bank automatically)
    new_words = fetch_gemini_words(level_name, min_l, max_l, missing_count, excluded)

    # 4. If still not enough, pull from the CSV as extra safety net
    if len(new_words) < missing_count:
        print(f"[Recruiter] Only {len(new_words)} words fetched. Supplementing from CSV...")
        try:
            with open(csv_path, mode="r", encoding="utf-8") as file:
                reader = csv.reader(file)
                all_csv_words = [row[0].strip().upper() for row in reader if row]

            already_fetched = {item["word"] for item in new_words}
            suitable_csv = [
                w for w in all_csv_words
                if min_l <= len(w) <= max_l
                and w not in excluded
                and w not in already_fetched
            ]
            random.shuffle(suitable_csv)
            for w in suitable_csv[: missing_count - len(new_words)]:
                new_words.append({"word": w, "sentence": f"Can you spell the word {w.lower()}?"})
        except Exception as e:
            print(f"[Recruiter] CSV fallback error: {e}")

    # 5. Populate learning pool with new words
    final_list = []

    # Existing words first
    for w in active_words:
        final_list.append({
            "word": w,
            "sentence": progress_data["learning_pool"][w].get("sentence", f"Spell {w}."),
        })

    # New words
    for item in new_words:
        word = item["word"]
        sentence = item["sentence"]
        if word not in progress_data["learning_pool"]:
            progress_data["learning_pool"][word] = {
                "correct_strikes": 0,
                "attempts": 0,
                "sentence": sentence,
            }
            final_list.append(item)
        if len(final_list) >= count:
            break

    return final_list[:count]


# ─────────────────────────────────────────────────────────────
#  PERSISTENCE
# ─────────────────────────────────────────────────────────────

def save_progress(progress_data, file_path=USER_PROGRESS_FILE):
    """Saves the player's Report Card to the JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(progress_data, f, indent=4)
    except Exception as e:
        print(f"[Save] Error: {e}")


def load_progress(file_path=USER_PROGRESS_FILE):
    """Loads the player's Report Card from JSON. Returns a fresh dict if not found."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "mastered_words": [],
            "learning_pool": {},
            "current_level": "Novice",
        }
