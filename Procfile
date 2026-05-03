# --workers 1 is REQUIRED — Chroma ships an embedded SQLite file and
# multiple workers would compete for the same write lock, eventually
# corrupting it. To scale beyond one process, swap Chroma for a
# managed Qdrant/Weaviate first.
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
