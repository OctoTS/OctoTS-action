#!/bin/bash

set -e

FORMAT=$1
INPUT=$2
OUTPUT=$3
BRANCH=$4

git fetch origin

if git ls-remote --exit-code --heads origin $BRANCH; then
  git checkout $BRANCH
  git pull origin $BRANCH
else
  git checkout --orphan $BRANCH
  git rm -rf .
fi

python3 "$OCTOTS_TOOLS_DIR/batchProcessor.py" append "$FORMAT" "$INPUT" "$OUTPUT"

git config user.email "github-actions[bot]@users.noreply.github.com"
git config user.name "github-actions[bot]"

git add $OUTPUT
git diff --quiet && git diff --staged --quiet || \
  (git commit -m "chore: update metrics [skip ci]" && git push origin $BRANCH)