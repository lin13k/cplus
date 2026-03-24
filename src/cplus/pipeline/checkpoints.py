"""Markdown checkpoint parsing from plan.md."""

from __future__ import annotations

import re
from pathlib import Path


def parse_checkpoints(plan_file: Path) -> list[str]:
    """Parse checkpoint blocks from plan.md.

    Extracts blocks that start with `## Checkpoint N: ...` headings.
    Each block includes all content until the next `## ` heading
    that isn't another Checkpoint.
    """
    if not plan_file.is_file():
        return []

    text = plan_file.read_text()
    lines = text.split("\n")
    checkpoints: list[str] = []
    current_block: list[str] = []
    in_checkpoint = False

    for line in lines:
        if re.match(r"^## Checkpoint \d+:", line):
            if in_checkpoint and current_block:
                checkpoints.append("\n".join(current_block))
            current_block = [line]
            in_checkpoint = True
        elif in_checkpoint:
            if line.startswith("## ") and not re.match(r"^## Checkpoint \d+:", line):
                checkpoints.append("\n".join(current_block))
                current_block = []
                in_checkpoint = False
            else:
                current_block.append(line)

    # Flush last block
    if in_checkpoint and current_block:
        checkpoints.append("\n".join(current_block))

    return checkpoints
