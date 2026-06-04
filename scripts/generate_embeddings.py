"""
generate_embeddings.py

Reads movie plots from MongoDB Atlas, generates vector embeddings via the
OpenAI API, and writes each embedding back onto its movie document.
"""

import os
import sys
import time
from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from openai import OpenAI

# --- Configuration ---
EMBEDDING_MODEL = "text-embedding-3-small"
# field whose text is embedded
SOURCE_FIELD = "plot"
# field where the embedding is stored
EMBEDDING_FIELD = "plot_embedding"

MOVIE_LIMIT = 20000
BATCH_SIZE = 100
# OpenAI call retry attempts
MAX_RETRIES = 3
# wait between retry attempts
RETRY_WAIT_SECONDS = 5

# --- Load secrets from .env ---
load_dotenv()
atlas_uri = os.getenv("ATLAS_URI")
openai_key = os.getenv("OPENAI_API_KEY")

if not atlas_uri:
    print("ERROR: ATLAS_URI not found in .env")
    sys.exit(1)

if not openai_key:
    print("ERROR: OPENAI_API_KEY not found in .env")
    sys.exit(1)

# --- Connect to OpenAI and MongoDB ---
openai_client = OpenAI(api_key=openai_key)
mongo_client = MongoClient(atlas_uri)
movies = mongo_client["sample_mflix"]["movies"]

# --- Select movies that have the source field and are not yet embedded ---
query = {
    SOURCE_FIELD: {"$exists": True, "$ne": ""},
    EMBEDDING_FIELD: {"$exists": False},
}
# Fetch only the fields used: _id (to update), title (for failure logging), source field (to embed)
projection = {"_id": 1, "title": 1, SOURCE_FIELD: 1}
cursor = movies.find(query, projection).limit(MOVIE_LIMIT)


# --- call the OpenAI API with retry ---
def embed_texts(texts):
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  calling OpenAI for batch of {len(texts)}...")
            response = openai_client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=texts,
                timeout=30,
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            if attempt < MAX_RETRIES:
                print(f"  attempt {attempt} failed ({e}); retrying in {RETRY_WAIT_SECONDS}s")
                time.sleep(RETRY_WAIT_SECONDS)
            else:
                raise


# --- State for processing ---
processed = 0
failed_movies = []


# --- embed and store one batch of movies ---
def process_batch(batch):
    global processed

    texts = [m[SOURCE_FIELD] for m in batch]

    # Embed the whole batch in one API call
    try:
        embeddings = embed_texts(texts)
    except Exception as e:
        for m in batch:
            failed_movies.append((m.get("title", "<untitled>"), str(e)))
        print(f"FAILED to embed batch of {len(batch)} -- {e}")
        return

    operations = []
    for movie, embedding in zip(batch, embeddings):
        operations.append(
            UpdateOne(
                {"_id": movie["_id"]},
                {"$set": {EMBEDDING_FIELD: embedding}},
            )
        )

    try:
        movies.bulk_write(operations)
        processed += len(operations)
        print(f"[{processed}] embedded so far...")
    except Exception as e:
        for m in batch:
            failed_movies.append((m.get("title", "<untitled>"), str(e)))
        print(f"FAILED to write batch of {len(batch)} -- {e}")


# --- Process the cursor in batches ---
batch = []
for movie in cursor:
    batch.append(movie)
    if len(batch) == BATCH_SIZE:
        process_batch(batch)
        batch = []

# Process any remaining movies that didn't fill a final batch
if batch:
    process_batch(batch)

# --- Summary ---
print(f"\nDone. Embedded: {processed}, Failed: {len(failed_movies)}")

if failed_movies:
    print("\n--- Failed movies ---")
    for title, error in failed_movies:
        print(f"  {title} -- {error}")

mongo_client.close()