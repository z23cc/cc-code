"""Fallback: python -m cc_flow. Prefer: cc-flow <command>."""

from cc_flow.entry import main

if __name__ == "__main__":
    main()
