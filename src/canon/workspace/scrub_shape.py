"""scrub_shape.py -- whether a value after a credential-bearing name is a secret.

The name-based rules match a name that carries a credential word (`password`,
`token`, `secret`, `key` and the rest) followed by `=` or `:` and a value. The
name says what the value is for. The value's shape says whether it is one:

- A number (at most 19 digits), a date or a time, a path, an AWS resource
  name (`arn:...`), or a boolean or null word is a setting after any name:
  `KEY_COUNT=1000`, `pass_rate=0.95`,
  `second pass: 2026-10-01`, `private_key_path: ~/.ssh/id_ed25519`. A path
  starts at `/`, `~/`, `./`, `../`, a drive letter or a variable, and none of
  its segments mixes upper case, lower case and a digit or runs to sixteen
  mixed-case letters, so a base64 key that happens to start with `/` is not
  read as a path.
- After a name that ends in a password word (`DB_PASSWORD`, `smtp_pass`), any
  other value is a secret. A person picks a password, and a word is a
  password.
- After a name that ends in another credential word (`GITHUB_TOKEN`,
  `client_secret`, `AWS_CREDENTIALS`), or in `key` after a credential word
  (`api_key`, `SECRET_KEY`), a short word of up to ten letters is a setting
  (`token: bearer`), since an issued key or token never reads as one. Anything
  else is a secret.
- After any other matching name, where a word follows the credential word
  (`token_type`, `KEY_PREFIX`, `session_token_ttl`) or the name is a bare
  `key` or `auth`, the value is a secret only when it looks random: twelve or
  more characters with no space that hold a run of eight or more letters and
  digits that is not a word followed by a number (`a8f3k2j9x7m1`, a hex
  digest), or that mix both cases with `+`, `/` or `=`. An identifier with a
  version, date or region digit (`kv-prod-eastus2`, `feature_flag_v2`) does
  not look random.

A number is a setting after a password word too, so a numeric PIN after
`password=` passes through: a declared limit.
"""
from __future__ import annotations

import re
from urllib.parse import unquote

PASSWORD = "password"
CREDENTIAL = "credential"
QUALIFIED = "qualified"

_PASSWORD_WORDS = frozenset({"password", "passwords", "passwd", "pwd", "pass", "passphrase"})
_PASSWORD_ENDINGS = ("password", "passwords", "passwd", "passphrase")
_CREDENTIAL_WORDS = frozenset({"token", "tokens", "secret", "secrets", "credential",
                               "credentials", "apikey", "apikeys"})
_KEY_WORDS = frozenset({"key", "keys"})
_KEY_CONTEXT = frozenset({"api", "access", "private", "client", "signing", "master",
                          "encryption", "account", "service", "auth"})
_NUMBER = re.compile(r"[+-]?(?:\d+(?:[_,]\d+)*)?(?:\.\d+)?(?:[eE][+-]?\d+)?")
_DATE = re.compile(r"\d{4}[-/]\d{2}[-/]\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?"
                   r"(?:Z|[+-]\d{2}:?\d{2})?)?|\d{1,2}:\d{2}(?::\d{2})?")
_PATH = re.compile(r"(?:~|\.{1,2}|[A-Za-z]:|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|%[A-Za-z_]\w*%)?"
                   r"[\\/](?:[\w.\-~@+]+[\\/])*[\w.\-~@+]*")
_ARN = re.compile(r"arn:[a-z0-9-]+:[a-z0-9-]+:[a-z0-9-]*:\d*:\S+")
_WORD = re.compile(r"[A-Za-z][a-z]{0,9}")
_URL = re.compile(r"[a-zA-Z][a-zA-Z0-9+.\-]*://")
_RUN = re.compile(r"[A-Za-z0-9]+")
# A word, a number, or a word followed by a number (`eastus2`, `v2`, `2024`,
# `GitHubUser42`), or a number followed by up to two letters (`64k`, `1st`).
_PLAIN_RUN = re.compile(r"[A-Za-z]*\d*|\d+[A-Za-z]{1,2}")
_BOOLEAN_WORDS = frozenset({"true", "false", "yes", "no", "on", "off", "none", "null", "nil"})


def name_segments(name: str) -> list[str]:
    """The lower-case words of a name: `apiKey`, `API_KEY` and `api-key` all
    give `api`, `key`."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return [s for s in re.split(r"[_.\-\s]+", spaced.lower()) if s]


def name_class(name: str) -> str:
    """PASSWORD or CREDENTIAL when the name ends in what it names, else
    QUALIFIED (the credential word is followed by another word, or the name
    is a bare `key` or `auth`, or it only contains a word such as `monkey`)."""
    segments = name_segments(name) or [""]
    last, before = segments[-1], segments[:-1]
    if last in _PASSWORD_WORDS or last.endswith(_PASSWORD_ENDINGS):
        return PASSWORD
    if last in _CREDENTIAL_WORDS or last.endswith(tuple(_CREDENTIAL_WORDS)):
        return CREDENTIAL
    if last in _KEY_WORDS and any(s in _KEY_CONTEXT or s in _CREDENTIAL_WORDS
                                  or s in _PASSWORD_WORDS for s in before):
        return CREDENTIAL
    return QUALIFIED


def _random_segment(segment: str) -> bool:
    mixed = re.search(r"[a-z]", segment) and re.search(r"[A-Z]", segment)
    return bool(mixed and (re.search(r"\d", segment) or len(segment) >= 16))


def is_path(value: str) -> bool:
    if not _PATH.fullmatch(value):
        return False
    return not any(_random_segment(s) for s in re.split(r"[\\/]", value))


def ordinary(value: str) -> bool:
    """A number, a date or time, a path, an AWS resource name, or a boolean or
    null word."""
    if value.lower() in _BOOLEAN_WORDS or _DATE.fullmatch(value) or is_path(value):
        return True
    if _ARN.fullmatch(value):
        return True
    digits = sum(c.isdigit() for c in value)
    return 0 < digits <= 19 and _NUMBER.fullmatch(value) is not None


def random_run(value: str) -> bool:
    """True when a run of eight or more letters and digits in `value` is not
    a word followed by a number: digits sit between letters (`a8f3k2j9`,
    `canaryV4lue`, a hex digest) or before more than two letters (`550e8400`).
    `kv-prod-eastus2`, `GitHubUser42` and `release-2026-10` have no such run."""
    return any(len(run) >= 8 and not _PLAIN_RUN.fullmatch(run) for run in _RUN.findall(value))


def looks_random(value: str) -> bool:
    """Twelve or more characters with no space, not a URL or an ordinary
    value, that hold a random run (`random_run`), or mix both cases with `+`,
    `/` or `=`."""
    if len(value) < 12 or re.search(r"\s", value) or _URL.match(value) or ordinary(value):
        return False
    if random_run(value):
        return True
    return bool(re.search(r"[a-z]", value) and re.search(r"[A-Z]", value)
                and re.search(r"[+/=]", value))


def shape_is_secret(value: str, kind: str) -> bool:
    """Whether `value`, after a name of class `kind`, is a secret."""
    if ordinary(value):
        return False
    if kind == PASSWORD:
        return True
    if kind == CREDENTIAL:
        return _WORD.fullmatch(value) is None
    return looks_random(value)


def userinfo_is_token(value: str) -> bool:
    """A URL user part with no password is a token when, with its percent
    escapes decoded, it holds a random run (`random_run`). A name such as
    `git`, `first.last`, `deploy-bot-2024`, `GitHubUser42` or an email address
    is not."""
    return random_run(unquote(value))


def cookie_is_secret(pairs: str) -> bool:
    """A cookie header is a secret when one of its values is: a value that
    looks random, or a secret-shaped value under a credential name. A consent
    or theme cookie is not."""
    for pair in pairs.split(";"):
        name, _, value = pair.strip().partition("=")
        value = value.strip().strip("\"")
        if not value or value.startswith("[REDACTED:"):
            continue
        kind = name_class(name)
        if looks_random(value) or (kind != QUALIFIED and shape_is_secret(value, kind)):
            return True
    return False
