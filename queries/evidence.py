"""
Records evidence from each search run into MongoDB.
"""

from datetime import datetime, timezone


EVIDENCE_DB = "sample_mflix"
EVIDENCE_COLLECTION = "search_evidence"


def _count_embedded_movies(mongo_client):
    # Counts movies with a plot_embedding
    movies = mongo_client[EVIDENCE_DB]["movies"]
    return movies.count_documents({"plot_embedding": {"$exists": True}})


def _format_top_results(results):
    # Making each result into "Title (year)"
    formatted = []
    for r in results:
        title = r.get("title", "<untitled>")
        year = r.get("year", "-")
        formatted.append(f"{title} ({year})")
    return formatted


def record_evidence(
    mongo_client,
    search_text,
    search_type,
    wall_clock_ms,
    results=None,
    error=None,
):
    """
    Write one evidence document
    """
    doc = {
        "timestamp": datetime.now(timezone.utc),
        "search_text": search_text,
        "search_type": search_type,
        "wall_clock_ms": wall_clock_ms,
    }

    try:
        doc["embedded_movie_count"] = _count_embedded_movies(mongo_client)
    except Exception as e:
        print(f"  (warning: could not count embedded movies for evidence: {e})")
        doc["embedded_movie_count"] = None

    if error is not None:
        doc["error"] = error
    else:
        doc["top_results"] = _format_top_results(results or [])

    try:
        mongo_client[EVIDENCE_DB][EVIDENCE_COLLECTION].insert_one(doc)
        print(f"  evidence recorded: {search_type}, {wall_clock_ms:.1f}ms")
    except Exception as e:
        print(f"  (warning: could not record evidence: {e})")