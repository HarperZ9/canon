"""hosts.py -- the text of a new instruction file canon is asked to create.

`canon switch --create` writes a file only when it does not exist yet; an
existing file is opted in by its owner adding the canon markers, never by canon.
A created file holds an empty canon region and, where the host needs one to
load the file at all, the header that makes it load.
"""
from __future__ import annotations

REGION = "<!-- canon:begin scope=workspace -->\n<!-- canon:end -->\n"


def new_host_text(target_name: str) -> str:
    """The initial text of a newly created instruction file for a target."""
    return REGION
