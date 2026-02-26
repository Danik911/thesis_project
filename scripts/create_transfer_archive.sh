#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
ARCHIVE_NAME="thesis_project_transfer_${TIMESTAMP}"
STAGING_ROOT="$(mktemp -d "/tmp/${ARCHIVE_NAME}_XXXXXX")"
STAGING_DIR="${STAGING_ROOT}/${ARCHIVE_NAME}"
ARCHIVE_PATH="${PROJECT_ROOT}/${ARCHIVE_NAME}.tar.gz"

cleanup() {
  if [[ -d "${STAGING_ROOT}" ]]; then
    rm -rf "${STAGING_ROOT}"
  fi
}
trap cleanup EXIT

require_command() {
  local cmd="$1"
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    echo "ERROR: Required command not found: ${cmd}" >&2
    exit 1
  fi
}

copy_dir_required() {
  local rel_path="$1"
  shift

  local src="${PROJECT_ROOT}/${rel_path}"
  local dest="${STAGING_DIR}/${rel_path}"

  if [[ ! -d "${src}" ]]; then
    echo "ERROR: Required directory missing: ${src}" >&2
    exit 1
  fi

  mkdir -p "$(dirname "${dest}")"
  rsync -a --prune-empty-dirs "$@" "${src}/" "${dest}/"
}

copy_file_optional() {
  local rel_path="$1"
  local src="${PROJECT_ROOT}/${rel_path}"
  local dest="${STAGING_DIR}/${rel_path}"

  if [[ -f "${src}" ]]; then
    mkdir -p "$(dirname "${dest}")"
    cp "${src}" "${dest}"
  fi
}

for required_cmd in rsync tar awk wc mktemp date; do
  require_command "${required_cmd}"
done

if [[ ! -f "${PROJECT_ROOT}/.env.example" ]]; then
  echo "ERROR: Missing required file: ${PROJECT_ROOT}/.env.example" >&2
  exit 1
fi

mkdir -p "${STAGING_DIR}"

copy_dir_required "main/src"
copy_dir_required "main/api"
copy_dir_required "main/frontend" \
  --exclude "node_modules" \
  --exclude ".next" \
  --exclude "out"
copy_dir_required "main/tests" --exclude "archive"
copy_dir_required "main/config"
copy_dir_required "main/scripts"
copy_dir_required "main/compliance"
copy_dir_required "main/analysis"
copy_dir_required "main/logs/audit"
copy_dir_required "main/logs/comprehensive_audit"
copy_dir_required "docs"
copy_dir_required "PRPs"
copy_dir_required "prompts"
copy_dir_required "scripts"
copy_dir_required ".github"
copy_dir_required "aws" \
  --exclude ".terraform" \
  --exclude "*.tfstate" \
  --exclude "*.tfstate.backup"
copy_dir_required "terraform" \
  --exclude ".terraform" \
  --exclude "*.tfstate" \
  --exclude "*.tfstate.backup"
copy_dir_required ".claude"

copy_file_optional "main/main.py"
copy_file_optional "main/__init__.py"

copy_file_optional "README.md"
copy_file_optional "CLAUDE.md"
copy_file_optional "LICENSE"
copy_file_optional "pyproject.toml"
copy_file_optional "uv.lock"
copy_file_optional "package.json"
copy_file_optional "docker-compose.dev.yml"
copy_file_optional "docker-compose.lims.yml"
copy_file_optional "docker-compose.bi.yml"
copy_file_optional "Dockerfile.api"
copy_file_optional "Dockerfile.frontend"
copy_file_optional "Dockerfile.worker"
copy_file_optional "start_server.sh"
copy_file_optional "TECHNICAL_ARCHITECTURE_REPORT.md"
copy_file_optional "optimized_category5_prompt.txt"

if [[ ! -f "${PROJECT_ROOT}/demo_data/MES_PPRS_PLANT_PERFORMANCE_2024_2025.csv" ]]; then
  echo "ERROR: Required BI demo file missing: demo_data/MES_PPRS_PLANT_PERFORMANCE_2024_2025.csv" >&2
  exit 1
fi
mkdir -p "${STAGING_DIR}/demo_data"
cp "${PROJECT_ROOT}/demo_data/MES_PPRS_PLANT_PERFORMANCE_2024_2025.csv" "${STAGING_DIR}/demo_data/"

cp "${PROJECT_ROOT}/.env.example" "${STAGING_DIR}/.env.example"
cp "${PROJECT_ROOT}/.env.example" "${STAGING_DIR}/.env.transfer"

cat > "${STAGING_DIR}/TRANSFER_README.md" <<'EOF'
# Transfer Package — Setup Guide

This package is a minimal transfer archive for the thesis project. It intentionally excludes rebuildable artifacts and all real secrets.

## Security First

- This archive includes `.env.example` and `.env.transfer` with placeholder values only.
- Do **not** send real API keys by email.
- Generate fresh keys in the target environment, or share secrets via a secure channel (Signal, password manager, encrypted note).

## Prerequisites

- Python 3.12+
- Node.js 18+
- `uv` (Python package manager)
- Docker + Docker Compose

## Setup Steps

1. Extract archive:

   ```bash
   tar xzf thesis_project_transfer_*.tar.gz
   cd thesis_project_transfer_*
   ```

2. Create local env file from placeholders:

   ```bash
   cp .env.transfer .env.local
   ```

3. Edit `.env.local` and set real keys (OpenRouter, LangFuse, Clerk, etc.).

4. Install Python dependencies:

   ```bash
   uv sync
   ```

5. Install frontend dependencies:

   ```bash
   cd main/frontend
   npm install
   cd ../..
   ```

6. Rebuild vector stores / RAG data (as needed):

   ```bash
  uv run python scripts/seed_chroma.py
  uv run python scripts/populate_lims_chroma.py
   ```

7. Start systems:

   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   docker-compose -f docker-compose.lims.yml up -d
   # BI local path:
   uv run uvicorn main.api.app:app --port 8080 --reload
   ```

## Excluded Artifacts and Rebuild Commands

| Excluded | Why Excluded | Rebuild |
|---|---|---|
| `.git/` | Git metadata | `git init` + add remote |
| `node_modules/` | Large dependency cache | `npm install` |
| `.venv/`, `.venv_ppocr/` | Local Python envs | `uv sync` |
| `main/chroma_db_v1020/`, `chroma_db_lims/` | Large generated vector DBs | `uv run python scripts/seed_chroma.py`, `uv run python scripts/populate_lims_chroma.py` |
| `aws/terraform/.terraform/` | Terraform plugins/cache | `terraform init` |
| `.next/`, `__pycache__/`, `.mypy_cache/`, coverage caches | Build/runtime caches | Regenerated automatically |
| `uploads/`, `output/`, runtime `logs/` | Runtime artifacts | Regenerated by app |

## Verification Quick Check

```bash
ls main/src main/api main/frontend docs PRPs .env.transfer TRANSFER_README.md
```

EOF

(
  cd "${STAGING_ROOT}"
  tar -czf "${ARCHIVE_PATH}" "${ARCHIVE_NAME}"
)

archive_size_bytes="$(wc -c < "${ARCHIVE_PATH}")"
archive_size_mb="$(awk "BEGIN {printf \"%.2f\", ${archive_size_bytes}/1024/1024}")"

echo "Archive created: ${ARCHIVE_PATH}"
echo "Archive size: ${archive_size_mb} MB"

max_email_bytes=$((25 * 1024 * 1024))
if [[ "${archive_size_bytes}" -le "${max_email_bytes}" ]]; then
  echo "Email compatibility: OK (< 25 MB)"
else
  echo "Email compatibility: WARNING (> 25 MB)"
fi

echo "Done."