"""Seed the vector store from the bundled demo knowledge bases.

Usage:
    python scripts/seed_knowledge_base.py            # all demos
    python scripts/seed_knowledge_base.py hotel      # just the hotel KB
    python scripts/seed_knowledge_base.py law        # just the law-firm KB

Idempotent — re-uploading the same file is detected by sha256 and skipped.
Safe to run after every code change to make the demo behave predictably.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.core.vectorstore import VectorStore  # noqa: E402
from app.db.database import Database  # noqa: E402
from app.ingestion.pipeline import IngestionPipeline  # noqa: E402

KB_ROOT = ROOT / "data" / "knowledge_base"


async def seed(folder: Path, pipeline: IngestionPipeline) -> tuple[int, int, int]:
    files = sorted(p for p in folder.glob("**/*") if p.suffix.lower() in {".md", ".markdown", ".txt", ".pdf"})
    if not files:
        print(f"  (no files in {folder})")
        return 0, 0, 0
    new = dup = chunks = 0
    for f in files:
        data = f.read_bytes()
        try:
            res = await pipeline.ingest_file(filename=f.name, data=data)
        except Exception as e:
            print(f"  ✗ {f.name}: {e}")
            continue
        if res.duplicate:
            dup += 1
            print(f"  · {f.name}: already indexed (doc #{res.document_id})")
        else:
            new += 1
            chunks += res.chunks
            print(f"  ✓ {f.name}: {res.chunks} chunks (doc #{res.document_id})")
    return new, dup, chunks


async def main(targets: list[str]) -> None:
    settings = get_settings()
    db = Database(settings.sqlite_path)
    await db.init()
    vs = VectorStore(settings.chroma_dir)
    pipeline = IngestionPipeline(
        db=db,
        vector_store=vs,
        upload_dir=settings.upload_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )

    folders: list[Path]
    if not targets:
        folders = [p for p in KB_ROOT.iterdir() if p.is_dir()]
    else:
        folders = [KB_ROOT / t for t in targets]

    for folder in folders:
        if not folder.is_dir():
            print(f"⚠ skipping {folder} — not a directory")
            continue
        print(f"\nSeeding from {folder.relative_to(ROOT)}")
        new, dup, chunks = await seed(folder, pipeline)
        print(f"  → {new} new, {dup} skipped, {chunks} chunks added")

    print(f"\nVector store now holds {vs.count()} chunks across {len(await db.list_documents())} documents.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="*", help="Subfolder names under data/knowledge_base/ (omit for all).")
    args = parser.parse_args()
    asyncio.run(main(args.targets))
