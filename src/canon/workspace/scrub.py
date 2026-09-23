"""scrub.py -- redact secret-shaped values before any text becomes a record.

A transcript holds whatever passed through the terminal: a pasted API key, a
bearer header in a curl command, a connection string with its password, a
`.env` line. None of it may reach a record, a brief or an instruction file.
`scrub` replaces each match with `[REDACTED:<code>]` and counts the hits by
code; it never stores the value or a digest of it, since a digest of a short
password can be reversed by guessing.

Coverage is pattern-based and deliberately broad: provider key formats
(Anthropic, OpenAI, GitHub, GitLab, Slack, AWS, Google, Stripe, Hugging Face,
npm), JSON web tokens, private key blocks, bearer and API-key headers,
credentials inside a connection URL, `password=` fields, and `NAME=value`
assignments whose name says key, token, secret, password or credential.
It does not prove a text is free of secrets; a secret with no recognisable
shape passes through. `find_secrets` is the same scan without the rewrite, used
as the last check before a store write and a render.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

REDACTED = "[REDACTED:{code}]"
_SECRET_WORD = r"(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|PWD|CREDENTIALS?)"
_PLACEHOLDER = re.compile(r"^(?:<.*|\$.*|\{.*|%.*|x+|\*+|\.+|changeme|your[_-].*|"
                          r"\[REDACTED:[a-z0-9-]+\].*)$", re.IGNORECASE)

# (code, pattern, group holding the secret; 0 means the whole match)
_RULES: tuple[tuple[str, re.Pattern[str], int], ...] = (
    ("private-key", re.compile(
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----(?:.*?-----END [A-Z0-9 ]*PRIVATE KEY-----|.*\Z)",
        re.DOTALL), 0),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}"), 0),
    ("openai-key", re.compile(r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{20,}"), 0),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{22,})"), 0),
    ("gitlab-token", re.compile(r"\bglpat-[A-Za-z0-9_\-]{20,}"), 0),
    ("slack-token", re.compile(r"\bxox[abposr]-[A-Za-z0-9\-]{10,}"), 0),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), 0),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"), 0),
    ("stripe-key", re.compile(r"\b(?:sk|rk)_(?:live|test)_[0-9A-Za-z]{16,}"), 0),
    ("huggingface-token", re.compile(r"\bhf_[A-Za-z0-9]{30,}"), 0),
    ("npm-token", re.compile(r"\bnpm_[A-Za-z0-9]{36}"), 0),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"), 0),
    ("bearer-header", re.compile(r"(?i)\bbearer\s+([A-Za-z0-9._~+/\-]{8,}=*)"), 1),
    ("api-key-header", re.compile(r"(?i)\b(?:x-api-key|api-key|x-auth-token)\s*[:=]\s*[\"']?([^\s\"',;]{8,})"), 1),
    ("connection-string", re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.\-]*://[^\s:/@\"']*:([^\s@/\"']+)@"), 1),
    ("password-field", re.compile(r"(?i)\b(?:password|passwd|pwd)\s*=\s*([^;\s\"'`]{4,})"), 1),
    ("json-secret", re.compile(
        r"(?i)\"[a-z0-9_\-]*(?:api[_-]?key|token|secret|password|passwd|credential)[a-z0-9_\-]*\"\s*:\s*\"([^\"]{4,})\""), 1),
    ("env-assignment", re.compile(
        rf"\b[A-Z][A-Z0-9_]*{_SECRET_WORD}[A-Z0-9_]*\s*[=:]\s*(\"[^\"\n]{{4,}}\"|'[^'\n]{{4,}}'|[^\s\"']{{4,}})"), 1),
)


@dataclass(frozen=True, slots=True)
class ScrubResult:
    text: str
    hits: dict[str, int]


def _secret_span(match: re.Match[str], group: int) -> tuple[int, int] | None:
    value = match.group(group)
    if not value:
        return None
    if group and _PLACEHOLDER.match(value.strip("\"'")):
        return None
    return match.span(group)


def scrub(text: str) -> ScrubResult:
    """`text` with every secret-shaped value redacted, and the hit count per
    rule. Rules run in order, so a provider key is named by its provider before
    the generic assignment rule sees the line."""
    hits: dict[str, int] = {}
    for code, pattern, group in _RULES:
        out: list[str] = []
        last = 0
        for match in pattern.finditer(text):
            span = _secret_span(match, group)
            if span is None:
                continue
            out.append(text[last:span[0]])
            out.append(REDACTED.format(code=code))
            last = span[1]
            hits[code] = hits.get(code, 0) + 1
        if out:
            out.append(text[last:])
            text = "".join(out)
    return ScrubResult(text, hits)


def find_secrets(text: str) -> list[str]:
    """The codes of every rule that still matches `text`, sorted."""
    found = set()
    for code, pattern, group in _RULES:
        if any(_secret_span(m, group) for m in pattern.finditer(text)):
            found.add(code)
    return sorted(found)


def secrets_in(value: object) -> list[str]:
    """`find_secrets` over every string inside a JSON-like value."""
    if isinstance(value, str):
        return find_secrets(value)
    items = value.values() if isinstance(value, dict) else value \
        if isinstance(value, list) else ()
    return sorted({code for item in items for code in secrets_in(item)})


def scrub_value(value: object, hits: dict[str, int]) -> object:
    """Scrub every string inside a JSON-like value, adding to `hits`."""
    if isinstance(value, str):
        result = scrub(value)
        for code, count in result.hits.items():
            hits[code] = hits.get(code, 0) + count
        return result.text
    if isinstance(value, list):
        return [scrub_value(item, hits) for item in value]
    if isinstance(value, dict):
        return {key: scrub_value(item, hits) for key, item in value.items()}
    return value
