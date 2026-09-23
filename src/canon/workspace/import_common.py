"""import_common.py -- what every transcript importer shares.

An importer reads a session file another tool wrote and proposes records. Four
rules hold for every importer:

1. Declared loss. Each importer names, in advance, every category of content it
   drops. Every line it reads is either used or counted under one of those
   categories. Content that fits no category (an entry type the importer has
   never seen) is an undeclared loss and refuses the import, unless the person
   running it declares that drop by name with `--drop-type`, which the report
   records.
2. Scrubbing. Every source string is scrubbed whole before any extraction rule
   reads it, so a length cap or a line break cannot cut a secret below the
   length its rule needs. Every candidate is scrubbed again after extraction,
   and the store refuses anything that still matches.
3. Project check. When the source names its repository or working directory,
   it must be this project, or the person must say `--accept-foreign-source`.
4. Proposals only. Imported records are written as proposed rows with an origin
   naming the source file, its digest, the line and the rule. Nothing renders
   until someone accepts it. A proposal already accepted, or rejected before, is
   not proposed again.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

from canon.versions import PIN_IMPORT_REPORT
from canon.workspace import authoring
from canon.workspace.extract import (
    Candidate,
    TextSeen,
    focus_candidate,
    plan_candidates,
    text_candidates,
)
from canon.workspace.scrub import merge_hits, scrub
from canon.workspace.identity import (
    METHOD_REMOTE,
    ProjectIdentity,
    ProjectIdentityError,
    normalize_remote,
)

REPORT_SCHEMA = PIN_IMPORT_REPORT.kind_tag
_SHORT = {"work-item": "task", "adr-decision": "decision",
          "environment-constraint": "constraint"}
DOES_NOT_PROVE = (
    "Proposals come from fixed text patterns. They are candidates for a person to "
    "accept or reject, not facts about the project.",
    "Text that matches no rule is not stored, so a decision or task phrased in "
    "another way is not proposed.",
    "The scrubber redacts secret-shaped values it recognises. It does not prove "
    "the source held no other sensitive text.",
)
# The drops every importer shares. Each importer adds its own categories.
COMMON_DROPS = {
    "unmatched-text": "a message text block that matched no extraction rule",
    "duplicate-candidate": "a candidate already proposed from an earlier line",
    "superseded-plan": "a plan tool call before the last one",
    "closed-plan-step": "a completed or empty plan step",
    "outside-area": "an edited file path outside the project root",
    "truncated-tail": "a final line cut off while the session was being written",
    "invalid-candidate": "a candidate that did not validate after scrubbing",
    "image": "an image or audio content part",
    "tool-call": "a tool call other than the plan tool and file edits; its input is not stored",
    "tool-output": "a tool result; its text is not stored",
}
MAX_AREAS = 10


class ImportRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


@dataclass(frozen=True, slots=True)
class Source:
    name: str
    sha256: str
    lines: tuple[tuple[int, dict, str], ...]
    line_count: int
    truncated_tail: bool


def read_jsonl(path: str | Path) -> Source:
    """Parse a JSONL session file. A malformed last line is a declared,
    reported truncation (a session still being written); a malformed line
    anywhere else refuses the import."""
    raw = Path(path).read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ImportRefused("unsupported_format", "the source is not UTF-8") from exc
    physical = text.split("\n")
    numbered = [(n, line) for n, line in enumerate(physical, start=1) if line.strip()]
    parsed, truncated = [], False
    for index, (n, line) in enumerate(numbered):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError as exc:
            if index == len(numbered) - 1:
                truncated = True
                continue
            raise ImportRefused("unsupported_format", f"line {n} is not JSON") from exc
        if not isinstance(obj, dict):
            raise ImportRefused("unsupported_format", f"line {n} is not a JSON object")
        parsed.append((n, obj, line))
    return Source(Path(path).name, hashlib.sha256(raw).hexdigest(), tuple(parsed),
                  len(numbered), truncated)


class Ledger:
    """Counts of what an importer dropped, by declared category, and the
    content it met that no category covers."""

    def __init__(self, declared: dict[str, str], user_drops: frozenset[str]) -> None:
        self.declared = declared
        self.user_drops = user_drops
        self.counts = {category: 0 for category in declared}
        self.user_counts: dict[str, int] = {}
        self.undeclared: dict[str, list[int]] = {}

    def drop(self, category: str, n: int = 1) -> None:
        if category not in self.declared:
            raise KeyError(f"{category!r} is not a declared drop")
        self.counts[category] += n

    def unknown(self, label: str, line: int) -> None:
        if label in self.user_drops:
            self.user_counts[label] = self.user_counts.get(label, 0) + 1
        else:
            self.undeclared.setdefault(label, []).append(line)


@dataclass
class Extraction:
    candidates: list[Candidate]
    ledger: Ledger
    session_id: str | None = None
    repository_url: str | None = None
    cwds: list[str] = field(default_factory=list)
    hits: dict[str, int] = field(default_factory=dict)


def project_check(identity: ProjectIdentity, extraction: Extraction) -> dict:
    """Whether the source says it belongs to this project. The report names
    the check and never a local path."""
    url = extraction.repository_url
    if url and identity.method == METHOD_REMOTE:
        try:
            key = normalize_remote(url)
        except ProjectIdentityError:
            key = None
        if key and not key.startswith("local:"):
            status = "match" if key == identity.key else "mismatch"
            return {"status": status, "by": "repository_url", "source_key": key}
    if extraction.cwds:
        root = os.path.normcase(os.path.normpath(str(identity.root)))
        inside = all(_inside(os.path.normcase(os.path.normpath(c)), root)
                     for c in extraction.cwds)
        return {"status": "match" if inside else "mismatch", "by": "working_directory"}
    return {"status": "unverified", "by": "none"}


def _inside(path: str, root: str) -> bool:
    return path == root or path.startswith(root.rstrip("\\/") + os.sep)


def relative_area(path: str, identity: ProjectIdentity) -> str | None:
    """A file path as a path inside the project, or None when it is outside."""
    root = os.path.normcase(os.path.normpath(str(identity.root)))
    target = os.path.normpath(path if os.path.isabs(path) else os.path.join(root, path))
    if not _inside(os.path.normcase(target), root) or os.path.normcase(target) == root:
        return None
    return os.path.relpath(target, str(identity.root)).replace("\\", "/")


def proposal_id(importer: str, key: str, cand: Candidate, index: int) -> str:
    if cand.kind == "workspace-focus":
        return authoring.FOCUS_ID
    digest = hashlib.sha256(f"{importer}\n{key}\n{cand.line}\n{cand.rule}\n{index}"
                            .encode("utf-8")).hexdigest()[:12]
    return f"imp-{_SHORT[cand.kind]}-{digest}"


@dataclass
class Collector:
    """Gathers what the rules find while an importer walks a session, then
    orders it: focus first, then the last plan's open steps, then text
    candidates in source order."""

    identity: ProjectIdentity
    ledger: Ledger
    seen: TextSeen = field(default_factory=TextSeen)
    text: list = field(default_factory=list)
    plans: list = field(default_factory=list)
    edits: dict = field(default_factory=dict)
    summary: tuple | None = None
    first_prompt: tuple | None = None
    branch: str | None = None
    hits: dict = field(default_factory=dict)

    def clean(self, text: str) -> str:
        """`text` scrubbed whole, its hits counted for the report."""
        result = scrub(text)
        merge_hits(self.hits, result.hits)
        return result.text

    def add_text(self, text: str, line: int, *, role: str) -> None:
        text = self.clean(text)
        if role == "user" and self.first_prompt is None and text.strip():
            self.first_prompt = (line, text.strip().splitlines()[0])
        found = text_candidates(text, line, self.seen)
        if found:
            self.text.extend(found)
        else:
            self.ledger.drop("unmatched-text")

    def add_plan(self, line: int, steps: list) -> None:
        self.plans.append((line, [(self.clean(str(text)), status) for text, status in steps]))

    def set_summary(self, line: int, text: str) -> None:
        self.summary = (line, self.clean(text))

    def add_edit(self, path: str) -> None:
        self.edits[path] = self.edits.get(path, 0) + 1

    def _areas(self) -> list:
        ranked = sorted(self.edits.items(), key=lambda kv: (-kv[1], kv[0]))
        areas = []
        for path, _count in ranked:
            area = relative_area(path, self.identity)
            if area is None:
                self.ledger.drop("outside-area")
            elif area not in areas and len(areas) < MAX_AREAS:
                areas.append(area)
        return areas

    def finish(self) -> list:
        self.ledger.drop("duplicate-candidate", self.seen.duplicates)
        plan_items = []
        if self.plans:
            self.ledger.drop("superseded-plan", len(self.plans) - 1)
            line, steps = self.plans[-1]
            plan_items, closed = plan_candidates(steps, line)
            self.ledger.drop("closed-plan-step", closed)
        areas = self._areas()
        focus = []
        if self.summary is not None:
            focus = [focus_candidate(self.summary[1], self.summary[0], "session-summary",
                                     branch=self.branch, areas=areas)]
        elif self.first_prompt is not None:
            focus = [focus_candidate(self.first_prompt[1], self.first_prompt[0],
                                     "first-prompt", branch=self.branch, areas=areas)]
        return focus + plan_items + self.text
