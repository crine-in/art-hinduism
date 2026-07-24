#!/usr/bin/env python3
"""
ART Hinduism Corpus — Maximum Parallel Dataset Generator
Organization: CRINE (www.crine.in)

Generates canonical ART scripture datasets for all 802 GRETIL texts in parallel
using all available CPU cores.
"""

import os
import sys
import time
from pathlib import Path

# Add tools directory to path
repo_root = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(repo_root / "tools"))

from build_art_datasets import main as build_main, process_item, load_json, save_json
import multiprocessing

def run_max_parallel():
    cpu_cores = os.cpu_count() or 4
    index_file = repo_root / "temp" / "gretil_index.json"
    
    if not index_file.exists():
        print(f"⚠️ Index file not found at {index_file}. Running parse_gretil_headers.py...")
        from parse_gretil_headers import main as parse_main
        parse_main()

    records = load_json(index_file) or []
    total_records = len(records)
    print(f"🚀 Starting dataset generation for all {total_records} GRETIL scripture texts...")
    print(f"⚡ Utilizing {cpu_cores} parallel CPU process workers.")
    
    start_time = time.time()

    # Arguments tuple for process_item
    tasks = [(rec, str(repo_root)) for rec in records]

    success_count = 0
    total_verses = 0

    with multiprocessing.Pool(processes=cpu_cores) as pool:
        for idx, result in enumerate(pool.starmap(process_item, tasks), 1):
            if result and "id" in result:
                success_count += 1
                total_verses += result.get("total_verses", 0)
                if idx % 20 == 0 or idx == total_records:
                    print(f"  [{idx}/{total_records}] ({idx/total_records*100:.1f}%) Completed: {result.get('title')} ({result.get('total_verses', 0):,} verses)")

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"🎉 Complete! Successfully generated {success_count}/{total_records} ART scripture datasets.")
    print(f"⏱️ Total Elapsed Time: {elapsed:.2f} seconds")
    print(f"📖 Total Verses Ingested: {total_verses:,}")
    print("=" * 60)

if __name__ == "__main__":
    run_max_parallel()
