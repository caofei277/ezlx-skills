#!/bin/bash
set -e

REPO_OWNER="caofei277"
REPO_NAME="ezlx-skills"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}"
BRANCH="main"
TARGET_DIR="$HOME/.config/opencode/skills"

if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed."
    exit 1
fi

mkdir -p "$TARGET_DIR"

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "==> Downloading ${REPO_NAME}..."
curl -fsSL "${REPO_URL}/archive/refs/heads/${BRANCH}.tar.gz" | tar -xzf - -C "$TEMP_DIR"

SKILLS_SOURCE="$TEMP_DIR/${REPO_NAME}-${BRANCH}/skills"

if [ ! -d "$SKILLS_SOURCE" ]; then
    echo "Error: skills/ directory not found in repository."
    exit 1
fi

if [ "$#" -gt 0 ]; then
    SKILL_NAMES=("$@")
else
    SKILL_NAMES=()
    for skill_dir in "$SKILLS_SOURCE"/*/; do
        [ -d "$skill_dir" ] || continue
        SKILL_NAMES+=("$(basename "$skill_dir")")
    done
fi

INSTALLED=0
FAILED=0

for SKILL_NAME in "${SKILL_NAMES[@]}"; do
    SOURCE_DIR="$SKILLS_SOURCE/$SKILL_NAME"

    if [ ! -d "$SOURCE_DIR" ]; then
        echo "Error: Skill '${SKILL_NAME}' not found."
        FAILED=$((FAILED + 1))
        continue
    fi

    if [ -d "$TARGET_DIR/$SKILL_NAME" ]; then
        echo "==> Updating: ${SKILL_NAME}"
        rm -rf "$TARGET_DIR/$SKILL_NAME"
    else
        echo "==> Installing: ${SKILL_NAME}"
    fi

    cp -r "$SOURCE_DIR" "$TARGET_DIR/$SKILL_NAME"

    if [ -f "$TARGET_DIR/$SKILL_NAME/SKILL.md" ]; then
        echo "    OK: ${SKILL_NAME} → ${TARGET_DIR}/${SKILL_NAME}/"
        INSTALLED=$((INSTALLED + 1))
    else
        echo "    Error: SKILL.md not found in ${SKILL_NAME}"
        FAILED=$((FAILED + 1))
    fi
done

echo ""
echo "==> Done: ${INSTALLED} installed, ${FAILED} failed"

[ "$FAILED" -gt 0 ] && exit 1
exit 0
