"""backflow_brief.py -- read edits to the brief block back as proposed records.

The brief canon writes into an instruction file is generated, but people and
agents edit it: they tick a task, add one, reword the goal, note a quirk. Each
line the brief renders has a fixed shape, so an edited line can be read back:

  Goal: <goal>                              -> the focus, with the new goal
  - [<status>] <title> (<id>)               -> that work item, new status or title
  - [<status>] <title>                      -> a new work item
  - [<category>] <statement> (<id>)         -> that constraint, updated
  - [<category>] <statement>                -> a new constraint
  a removed work line                       -> that work item, status dropped

A line that fits none of these is not guessed at. All such lines together
become one proposed memory record holding the text as written, so an edit is
never lost and never silently turned into something else. Lines labelled
`[global]` or `[from <project>]` belong to another scope and are treated as
unmapped. Removals are read only against canon's own last render; without one,
an absent line says nothing.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

from canon.schema import (
    CONSTRAINT_CATEGORIES,
    KIND_ENVIRONMENT_CONSTRAINT,
    KIND_EPISODIC_MEMORY,
    KIND_WORK_ITEM,
    KIND_WORKSPACE_FOCUS,
    WORK_ITEM_STATUSES,
    Record,
)

_SECTION_RE = re.compile(r"^#{2,3} (Focus|Open work|Decisions|Constraints and quirks|Left out)$")
_TAG = r"(?P<tag> \[(?:global|from prj_[0-9a-f]{32})\])?"
_ITEM_RE = re.compile(r"^- \[(?P<mark>[a-z-]+)\] (?P<text>.+?)"
                      r"(?: \((?P<id>[a-z0-9][a-z0-9-]*)\))?" + _TAG + r"$")
_GOAL_RE = re.compile(r"^Goal: (?P<text>.+?)" + _TAG + r"$")


@dataclass(frozen=True, slots=True)
class Edit:
    """One in-place edit read back from a region: the rule that read it, the
    record it proposes (kind, id or None for a new one, data), the file line,
    and whether it retires the record."""

    rule: str
    kind: str
    rid: str | None
    data: dict
    line: int
    retire: bool = False


def _sections(body: str) -> list[tuple[str, str]]:
    section, out = "", []
    for line in body.split("\n"):
        heading = _SECTION_RE.match(line)
        if heading:
            section = heading.group(1)
        out.append((section, line))
    return out


def _work(match, records: dict, line: int) -> Edit | None:
    status, title, rid = match["mark"], match["text"], match["id"]
    if status not in WORK_ITEM_STATUSES:
        return None
    current = records.get(rid)
    if rid and current is not None and current.kind == KIND_WORK_ITEM:
        return Edit("brief-work", KIND_WORK_ITEM, rid,
                    {**current.data, "status": status, "title": title}, line)
    if rid:
        return None
    return Edit("brief-new-work", KIND_WORK_ITEM, None, {"title": title, "status": status}, line)


def _constraint(match, records: dict, line: int) -> Edit | None:
    category, statement, rid = match["mark"], match["text"], match["id"]
    if category not in CONSTRAINT_CATEGORIES:
        return None
    current = records.get(rid)
    if rid and current is not None and current.kind == KIND_ENVIRONMENT_CONSTRAINT:
        return Edit("brief-constraint", KIND_ENVIRONMENT_CONSTRAINT, rid,
                    {**current.data, "category": category, "statement": statement}, line)
    if rid:
        return None
    return Edit("brief-new-constraint", KIND_ENVIRONMENT_CONSTRAINT, None,
                {"statement": statement, "category": category}, line)


def _map_line(section: str, text: str, records: dict, line: int) -> Edit | None:
    if section == "Focus":
        goal = _GOAL_RE.match(text)
        if goal and not goal["tag"]:
            current = records.get("focus")
            base = dict(current.data) if current is not None else {}
            return Edit("brief-focus", KIND_WORKSPACE_FOCUS, "focus",
                        {**base, "goal": goal["text"]}, line)
        return None
    item = _ITEM_RE.match(text)
    if item is None or item["tag"]:
        return None
    if section == "Open work":
        return _work(item, records, line)
    if section == "Constraints and quirks":
        return _constraint(item, records, line)
    return None


def _removed_work(removed: list[tuple[str, str]], mapped_ids: set, records: dict,
                  line: int) -> list[Edit]:
    edits = []
    for section, text in removed:
        item = _ITEM_RE.match(text)
        if item is None or item["tag"]:
            continue  # another scope's line: it never names this project's record
        rid = item["id"] if section == "Open work" else None
        current = records.get(rid)
        if rid and rid not in mapped_ids and current is not None \
                and current.kind == KIND_WORK_ITEM:
            edits.append(Edit("brief-removed-work", KIND_WORK_ITEM, rid,
                              {**current.data, "status": "dropped"}, line))
    return edits


def brief_edits(actual: str, base: str, first_line: int, records: list[Record], *,
                has_base: bool) -> list[Edit]:
    """Every edit between the brief body canon wrote (`base`) and the one on
    disk (`actual`), mapped to proposed records. `first_line` is the file line
    number of the body's first line."""
    by_id = {r.id: r for r in records}
    remaining = Counter(_sections(base))
    added: list[tuple[int, str, str]] = []
    for index, (section, text) in enumerate(_sections(actual)):
        if remaining[(section, text)] > 0:
            remaining[(section, text)] -= 1
        elif text.strip():
            added.append((first_line + index, section, text))
    edits, unmapped = [], []
    for line, section, text in added:
        edit = _map_line(section, text, by_id, line)
        if edit is None:
            unmapped.append((line, text))
        else:
            edits.append(edit)
    if has_base:
        removed = [key for key, count in remaining.items() for _ in range(count)]
        mapped = {e.rid for e in edits if e.rid}
        edits += _removed_work(removed, mapped, by_id, first_line)
    if unmapped:
        edits.append(Edit("unmapped-edit", KIND_EPISODIC_MEMORY, None,
                          {"layer": "L0", "text": "\n".join(t for _, t in unmapped),
                           "source_ids": []}, unmapped[0][0]))
    return edits
