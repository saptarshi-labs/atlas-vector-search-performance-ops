#!/bin/bash
#
# run.sh
# Menu launcher for the project's operational tasks.
# Run from the repo root.

cd "$(dirname "$0")"
source .venv/bin/activate

ATLAS_URI=$(grep '^ATLAS_URI=' .env | cut -d= -f2-)
CLUSTER_NAME="vector-search-performance"


while true; do
    echo ""
    echo "Atlas Vector Search Performance Ops"
    echo "  1) Load Sample Database"
    echo "  2) Generate Embeddings"
    echo "  3) Run a Validation Search"
    echo "  4) Import Synthetic Data"
    echo "  5) Export Evidence"
    echo "  6) Quit"
    read -rp "Choice: " choice

    case "$choice" in
        1)
            atlas clusters loadSampleData "$CLUSTER_NAME"
            ;;
        2)
            cd scripts && python3 generate_embeddings.py && cd ..
            ;;
        3)
            echo "  1) Vector  2) Text  3) Hybrid"
            read -rp "Choice: " s
            cd queries
            case "$s" in
                1) python3 vector_search.py ;;
                2) python3 text_search.py ;;
                3) python3 hybrid_search.py ;;
            esac
            cd ..
            ;;
        4)
            mongoimport --uri "$ATLAS_URI" \
                --db sample_mflix --collection movies \
                --file scripts/synthetic_movies.jsonl
            ;;
        5)
            mkdir -p evidence
            mongoexport --uri "$ATLAS_URI" \
                --db sample_mflix --collection search_evidence \
                --out evidence/search_evidence.json
            ;;
        6)
            exit 0
            ;;
    esac
done
