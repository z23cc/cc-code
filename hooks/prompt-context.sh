#!/bin/bash
# UserPromptSubmit hook: inject relevant context based on user's message.
# Detects epic/task IDs and auto-loads specs, detects keywords for routing hints.

INPUT=$(cat)
MESSAGE=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('user_message',''))" 2>/dev/null)

[ -z "$MESSAGE" ] && exit 0

# Detect epic/task IDs (epic-N, epic-N.M, fn-N, fn-N.M)
TASK_ID=$(echo "$MESSAGE" | grep -oE '(epic|fn)-[0-9]+[-a-z]*\.[0-9]+' | head -1)
EPIC_ID=$(echo "$MESSAGE" | grep -oE '(epic|fn)-[0-9]+[-a-z]*' | head -1)

CONTEXT=""

# Auto-load task spec if ID detected
if [ -n "$TASK_ID" ]; then
  SPEC_FILE=".tasks/tasks/${TASK_ID}.json"
  if [ -f "$SPEC_FILE" ]; then
    TITLE=$(python3 -c "import json; d=json.load(open('$SPEC_FILE')); print(d.get('title',''))" 2>/dev/null)
    STATUS=$(python3 -c "import json; d=json.load(open('$SPEC_FILE')); print(d.get('status',''))" 2>/dev/null)
    CONTEXT="Task ${TASK_ID}: ${TITLE} [${STATUS}]"
  fi
elif [ -n "$EPIC_ID" ]; then
  EPIC_FILE=".tasks/epics/${EPIC_ID}.md"
  if [ -f "$EPIC_FILE" ]; then
    TITLE=$(head -3 "$EPIC_FILE" | grep -oP '(?<=# ).*' | head -1)
    CONTEXT="Epic ${EPIC_ID}: ${TITLE}"
  fi
fi

# Output context if found
if [ -n "$CONTEXT" ]; then
  echo "$CONTEXT"
fi

exit 0
