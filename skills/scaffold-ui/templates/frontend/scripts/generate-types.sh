#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# Generate TypeScript types from FastAPI OpenAPI spec.
#
# Usage:
#   bash scripts/generate-types.sh
#   bash scripts/generate-types.sh http://api.example.com/openapi.json
#
# Prerequisites:
#   npm install -D openapi-typescript
# ═══════════════════════════════════════════════════════════════

set -e

API_URL="${1:-http://localhost:8000/openapi.json}"
OUTPUT_FILE="src/types/api.ts"

echo "🔄 Generating TypeScript types from: $API_URL"

npx -y openapi-typescript "$API_URL" -o "$OUTPUT_FILE"

echo "✅ Types generated: $OUTPUT_FILE"
echo "   Import with: import type { paths, components } from '@/types/api'"
