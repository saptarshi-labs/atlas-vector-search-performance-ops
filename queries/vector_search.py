"""
Semantic (vector) search on sample_mflix.movies.
Embeds the query with OpenAI, then finds movies whose plot_embedding
is most similar via Atlas $vectorSearch.
"""

import os
import sys
import time
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI

from evidence import record_evidence


EMBEDDING_MODEL = "text-embedding-3-small"
INDEX_NAME = "plot_vector_index"
EMBEDDING_FIELD = "plot_embedding"
NUM_CANDIDATES = 100
NUM_RESULTS = 5


load_dotenv()
atlas_uri = os.getenv("ATLAS_URI")
openai_key = os.getenv("OPENAI_API_KEY")

if not atlas_uri or not openai_key:
    print("ERROR: ATLAS_URI or OPENAI_API_KEY not found in .env")
    sys.exit(1)


openai_client = OpenAI(api_key=openai_key)
mongo_client = MongoClient(atlas_uri)
movies = mongo_client["sample_mflix"]["movies"]


QUERY_TEXT = input("Enter your search query: ").strip()

if not QUERY_TEXT:
    print("ERROR: search query cannot be empty.")
    sys.exit(1)


print("\nOptional filters — press Enter to skip any of them:")

actor    = input("  Actor name (exact)    : ").strip()
director = input("  Director name (exact) : ").strip()
genre    = input("  Genre (exact)         : ").strip()
min_year = input("  Minimum year          : ").strip()


conditions = []
filter_labels = []

if actor:
    conditions.append({"cast": actor})
    filter_labels.append(f"actor = {actor}")

if director:
    conditions.append({"directors": director})
    filter_labels.append(f"director = {director}")

if genre:
    conditions.append({"genres": genre})
    filter_labels.append(f"genre = {genre}")

if min_year:
    if min_year.isdigit():
        conditions.append({"year": {"$gte": int(min_year)}})
        filter_labels.append(f"year >= {min_year}")
    else:
        print(f"  (ignored: '{min_year}' is not a valid year)")


# Embed the query text
response = openai_client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=QUERY_TEXT,
)
query_vector = response.data[0].embedding


vector_stage = {
    "index": INDEX_NAME,
    "path": EMBEDDING_FIELD,
    "queryVector": query_vector,
    "numCandidates": NUM_CANDIDATES,
    "limit": NUM_RESULTS,
}

if conditions:
    if len(conditions) == 1:
        vector_stage["filter"] = conditions[0]
    else:
        vector_stage["filter"] = {"$and": conditions}

pipeline = [
    {"$vectorSearch": vector_stage},
    {
        "$project": {
            "_id": 0,
            "title": 1,
            "year": 1,
            "genres": 1,
            "runtime": 1,
            "cast": 1,
            "directors": 1,
            "imdb.rating": 1,
            "plot": 1,
            "fullplot": 1,
        }
    },
]


# Query Execution Time Calculation
start = time.perf_counter()
results = list(movies.aggregate(pipeline))
wall_clock_ms = (time.perf_counter() - start) * 1000


applied = "  +  ".join(filter_labels) if filter_labels else "none"

print(f"\n{'=' * 70}")
print(f'  Search results for: "{QUERY_TEXT}"')
print(f"  Filters: {applied}")
print(f"{'=' * 70}\n")

if not results:
    print("  No matching movies found.")
    if conditions:
        print("  Tip: filters use exact matching. Check spelling/case, and note")
        print("  some filter combinations may legitimately match nothing.\n")
    else:
        print()
else:
    for i, movie in enumerate(results, start=1):
        title    = movie.get("title", "Untitled")
        year     = movie.get("year", "—")

        runtime  = movie.get("runtime")
        runtime  = f"{runtime} min" if runtime else "—"

        genres   = ", ".join(movie.get("genres", [])) or "—"
        rating   = movie.get("imdb", {}).get("rating") or "—"
        cast     = ", ".join(movie.get("cast", [])[:4]) or "—"
        director = ", ".join(movie.get("directors", [])) or "—"
        desc     = movie.get("fullplot") or movie.get("plot", "(no description available)")

        print(f"  {i}. {title}  ({year})")
        print(f"     {genres}  |  {runtime}  |  IMDb: {rating}")
        print(f"     Director: {director}")
        print(f"     Cast: {cast}")
        print(f"     {desc}")
        print(f"  {'-' * 66}\n")


record_evidence(
    mongo_client,
    search_text=QUERY_TEXT,
    search_type="vector",
    wall_clock_ms=wall_clock_ms,
    results=results,
)


mongo_client.close()