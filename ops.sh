#!/bin/bash
#
# ops.sh
# Menu launcher for the project's operational tasks.

cd "$(dirname "$0")"
source .venv/bin/activate

ATLAS_URI=$(grep '^ATLAS_URI=' .env | cut -d= -f2-)
CLUSTER_NAME="vector-search-performance"


while true; do
    echo ""
    echo "Atlas Vector Search Performance Ops"
    echo "  1) Load Sample Database"
    echo "  2) Generate Embeddings"
    echo "  3) Create Vector Index"
    echo "  4) Create Text Index"
    echo "  5) Run a Validation Search"
    echo "  6) Import Synthetic Data"
    echo "  7) Export Evidence"
    echo "  8) Quit"
    read -rp "Choice: " choice

    case "$choice" in
        1)
            atlas clusters sampleData load "$CLUSTER_NAME"
            ;;
        2)
            cd scripts && python3 generate_embeddings.py && cd ..
            ;;
        3)
            atlas clusters search indexes create \
                --clusterName "$CLUSTER_NAME" \
                --file index_definitions/vector_index.json
            ;;
        4)
            atlas clusters search indexes create \
                --clusterName "$CLUSTER_NAME" \
                --file index_definitions/text_index.json
            ;;
        5)
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
        6)
            mongoimport --uri "$ATLAS_URI" \
                --db sample_mflix --collection movies \
                --file scripts/synthetic_movies.jsonl
            ;;
        7)
            mkdir -p evidence
            mongoexport --uri "$ATLAS_URI" \
                --db sample_mflix --collection search_evidence \
                --out evidence/search_evidence.json
            ;;
        8)
            exit 0
            ;;
    esac
done