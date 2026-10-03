#!/bin/bash
# Patent Yard: copy the worldwide patent table from BigQuery to this Mac (run it yourself in Terminal).
#  1. BigQuery writes the table patentyard.world into gs://patentyard-export-cf5d9a01/world/ as gzipped JSON files
#     (exports are free in BigQuery; the few GB of storage come out of the free trial credit).
#  2. The files are downloaded to pipeline/raw/world/parts/ (download fees, a few dollars at most, also come out of
#     the free trial credit; a free-trial account is never billed unless you click Upgrade).
set -e
cd "$(dirname "$0")"
./bqx bq --location=US extract --destination_format=NEWLINE_DELIMITED_JSON --compression=GZIP \
  project-cf5d9a01-3ee2-47d4-a00:patentyard.world 'gs://patentyard-export-cf5d9a01/world/part-*.json.gz'
mkdir -p raw/world/parts
./bqx gcloud storage cp 'gs://patentyard-export-cf5d9a01/world/*' raw/world/parts/
echo "Done: $(ls raw/world/parts | wc -l) files, $(du -sh raw/world/parts | cut -f1)"
