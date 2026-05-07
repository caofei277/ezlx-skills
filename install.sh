#!/bin/bash
set -e

REPO_OWNER="caofei277"
REPO_NAME="ezlx-skills"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}"
BRANCH="main"
SKILL_NAME="opencode-cross-platform-setup"
TARGET_DIR="$HOME/.config/opencode/skills"

echo "==> Installing skill: ${SKILL_NAME}"
echo "==> Target: ${TARGET_DIR}/${SKILL_NAME}/"

if ! command -v curl &> /dev/null; then
    echo "Error: curl is required but not installed."
    exit 1
fi

mkdir -p "$TARGET_DIR"

TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "==> Downloading ${REPO_NAME}..."
curl -fsSL "${REPO_URL}/archive/refs/heads/${BRANCH}.tar.gz" | tar -xzf - -C "$TEMP_DIR"

SOURCE_DIR="$TEMP_DIR/${REPO_NAME}-${BRANCH}/skills/${SKILL_NAME}"
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Skill '${SKILL_NAME}' not found in repository."
    exit 1
fi

if [ -d "$TARGET_DIR/$SKILL_NAME" ]; then
    echo "==> Updating existing skill..."
    rm -rf "$TARGET_DIR/$SKILL_NAME"
fi

cp -r "$SOURCE_DIR" "$TARGET_DIR/$SKILL_NAME"

if [ -f "$TARGET_DIR/$SKILL_NAME/SKILL.md" ]; then
    echo "==> OK: ${SKILL_NAME} installed successfully"
    echo "    Location: ${TARGET_DIR}/${SKILL_NAME}/"
else
    echo "Error: Installation failed - SKILL.md not found"
    exit 1
fi
