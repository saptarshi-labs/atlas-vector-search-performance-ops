"""
generate_synthetic_movies.py
Generates synthetic movie documents for the scaling experiment and writes
them to a JSONL file, later loaded into the movies collection with mongoimport.
"""

import json
import random

# --- Configuration ---
MOVIE_COUNT = 20000
POOLS_FILE = "synthetic_data_pools.json"
OUTPUT_FILE = "synthetic_movies.jsonl"
YEAR_MIN = 1950
YEAR_MAX = 2025

# --- Load the word pools from the data file ---
with open(POOLS_FILE, "r", encoding="utf-8") as f:
    pools = json.load(f)


def make_name():
    """Return a single random full name."""
    return random.choice(pools["first_names"]) + " " + random.choice(pools["last_names"])


def make_title():
    """Return a random two-word title."""
    return random.choice(pools["title_first_word"]) + " " + random.choice(pools["title_second_word"])


def make_plot():
    """Return a short one-sentence plot built from three word pools."""
    character = random.choice(pools["plot_characters"])
    action = random.choice(pools["plot_actions"])
    obstacle = random.choice(pools["plot_obstacles"])
    return f"A {character} must {action} despite {obstacle}."


def make_fullplot(plot):
    """Return a longer plot: an opening line followed by the short plot."""
    opening = random.choice(pools["fullplot_openings"])
    return f"{opening}, a story begins. {plot}"


def make_movie():
    """Build one synthetic movie document as a dict."""
    plot = make_plot()
    return {
        "title": make_title(),
        "plot": plot,
        "fullplot": make_fullplot(plot),
        "genres": random.sample(pools["genres"], random.randint(1, 3)),
        "cast": [make_name() for _ in range(random.randint(2, 4))],
        "directors": [make_name() for _ in range(random.randint(1, 2))],
        "year": random.randint(YEAR_MIN, YEAR_MAX),
    }


# --- Generate and write ---
written = 0

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    for _ in range(MOVIE_COUNT):
        movie = make_movie()
        f.write(json.dumps(movie) + "\n")
        written += 1

print(f"Done. Wrote {written} synthetic movies to {OUTPUT_FILE}")