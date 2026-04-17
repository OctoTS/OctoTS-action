#!/bin/bash

set -e

FORMAT=$1
INPUT=$2
OUTPUT=$3
BRANCH=$4

echo "Configuring git..."
git config --global user.email "github-actions[bot]@users.noreply.github.com"
git config --global user.name "github-actions[bot]"
git config --global --add safe.directory /github/workspace

echo "Preparing branch..."
git fetch origin

if git ls-remote --exit-code --heads origin "$BRANCH"; then
  git checkout "$BRANCH"
  git pull origin "$BRANCH"
else
  git checkout --orphan "$BRANCH"
  git rm -rf .
fi

echo "Running processor..."
python3 /app/batchProcessor.py append "$FORMAT" "$INPUT" "$OUTPUT"

echo "Committing changes..."
git add "$OUTPUT"
git diff --quiet && git diff --staged --quiet || \
  (git commit -m "chore: update metrics [skip ci]" && git push origin "$BRANCH")