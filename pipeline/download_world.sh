#!/bin/bash
# Patent Yard: finish downloading the exported worldwide patent files (run it yourself in Terminal).
# One process with many threads (several processes hang on macOS); files already downloaded are skipped.
set -e
cd "$(dirname "$0")"
mkdir -p raw/world/parts
export CLOUDSDK_STORAGE_PROCESS_COUNT=1 CLOUDSDK_STORAGE_THREAD_COUNT=24
caffeinate -i ./bqx gcloud storage cp --no-clobber 'gs://patentyard-export-cf5d9a01/world/*' raw/world/parts/
echo "Done: $(ls raw/world/parts/*.json.gz | wc -l) files, $(du -sh raw/world/parts | cut -f1)"
