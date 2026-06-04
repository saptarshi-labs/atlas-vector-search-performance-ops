"""
Hybrid search on sample_mflix.movies: combines semantic vector search
($vectorSearch) with full-text keyword search ($search), fused via the
native $rankFusion stage. Title matches are boosted over plot matches
in the text pipeline.

"""

import os
import sys
import time
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI

from evidence import record_evidence


EMBEDDING_MODEL = "text-embedding-3-small"
VECTOR_INDEX = "plot_vector_index"
TEXT_INDEX = "plot_text_index"
EMBEDDING_FIELD = "plot_embedding"
NUM_CANDIDATES = 100
NUM_RESULTS = 5

VECTOR_WEIGHT = 0.5
TEXT_WEIGHT = 0.5


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


# Embed the query
response = openai_client.embeddings.create(
    model=EMBEDDING_MODEL,
    input=QUERY_TEXT,
)
query_vector = response.data[0].embedding


pipeline = [
    {
        "$rankFusion": {
            "input": {
                "pipelines": {
                    "vectorPipeline": [
                        {
                            "$vectorSearch": {
                                "index": VECTOR_INDEX,
                                "path": EMBEDDING_FIELD,
                                "queryVector": query_vector,
                                "numCandidates": NUM_CANDIDATES,
                                "limit": NUM_RESULTS,
                            }
                        }
                    ],
                    "textPipeline": [
                        {
                            "$search": {
                                "index": TEXT_INDEX,
                                "compound": {
                                    "should": [
                                        {
                                            "text": {
                                                "query": QUERY_TEXT,
                                                "path": "title",
                                                "score": {"boost": {"value": 3}},
                                            }
                                        },
                                        {
                                            "text": {
                                                "query": QUERY_TEXT,
                                                "path": "plot",
                                            }
                                        },
                                    ]
                                },
                            }
                        },
                        {"$limit": NUM_RESULTS},
                    ],
                }
            },
            "combination": {
                "weights": {
                    "vectorPipeline": VECTOR_WEIGHT,
                    "textPipeline": TEXT_WEIGHT,
                }
            },
        }
    },
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
    {"$limit": NUM_RESULTS},
]


# Query Execution Time Calculation
results = []
error_message = None
start = time.perf_counter()
try:
    results = list(movies.aggregate(pipeline))
except Exception as e:
    error_message = f"{type(e).__name__}: {e}"
wall_clock_ms = (time.perf_counter() - start) * 1000


print(f"\n{'=' * 70}")
print(f'  Hybrid search results for: "{QUERY_TEXT}"')
print(f"  (vector weight {VECTOR_WEIGHT}, text weight {TEXT_WEIGHT})")
print(f"{'=' * 70}\n")

if error_message:
    print(f"  Hybrid search failed: {error_message}\n")
elif not results:
    print("  No matching movies found.\n")
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
    search_type="hybrid",
    wall_clock_ms=wall_clock_ms,
    results=results if not error_message else None,
    error=error_message,
)


mongo_client.close()