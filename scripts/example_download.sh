#!/usr/bin/env bash
set -euo pipefail

# Example: Download dataset with new unified API
# Usage: ./example_download.sh <dataset_id> <token>

if [[ -z "${DS_API_BASE_URL:-}" ]]; then
  echo "Error: DS_API_BASE_URL not set"
  echo "Example: export DS_API_BASE_URL='http://localhost:3003'"
  exit 1
fi

if [[ -z "${DS_RUNTIME_KEY_SECRET:-}" ]]; then
  echo "Error: DS_RUNTIME_KEY_SECRET not set"
  echo "This should match the backend DECRYPT_RUNTIME_ENVIRONMENT_SECRET"
  echo "Example: export DS_RUNTIME_KEY_SECRET='your-shared-secret'"
  exit 1
fi

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <dataset_id> <token> [columns] [limit]"
  echo ""
  echo "Examples:"
  echo "  $0 demo-dataset-001 \$TOKEN"
  echo "  $0 medical_imaging_2024 \$TOKEN 'patient_id,diagnosis' 100"
  exit 1
fi

dataset_id="$1"
token="$2"
columns="${3:-}"
limit="${4:-}"

# Build command
cmd="python -m delong_datasets download \"$dataset_id\" --token \"$token\""

if [[ -n "$columns" ]]; then
  cmd="$cmd --columns $columns"
fi

if [[ -n "$limit" ]]; then
  cmd="$cmd --limit $limit"
fi

echo "Downloading dataset: $dataset_id"
echo "Command: $cmd"
echo ""

eval "$cmd"


