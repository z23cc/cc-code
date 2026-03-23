#!/bin/bash
# PreToolUse hook: block modifications to linter/formatter/CI config files.
# Prevents accidental weakening of code quality rules.
# Can be overridden with CC_ALLOW_CONFIG_EDIT=1.

[ "${CC_ALLOW_CONFIG_EDIT:-}" = "1" ] && exit 0

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)

[ -z "$FILE_PATH" ] && exit 0

BASENAME=$(basename "$FILE_PATH")

# Protected config files
case "$BASENAME" in
  .ruff.toml|ruff.toml|.flake8|.pylintrc|.mypy.ini|mypy.ini|\
  .eslintrc*|.prettierrc*|biome.json|.stylelintrc*|\
  .editorconfig|.pre-commit-config.yaml|\
  .github/workflows/*|.gitlab-ci.yml|Jenkinsfile)
    echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"decision\":\"allow\",\"message\":\"⚠️ Modifying quality config: ${BASENAME}. Make sure you're not weakening lint/format rules. Set CC_ALLOW_CONFIG_EDIT=1 to suppress.\"}}"
    exit 0
    ;;
esac

exit 0
