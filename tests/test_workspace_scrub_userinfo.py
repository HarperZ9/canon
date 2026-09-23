"""A URL's user part: the password of any `user:password@` is redacted, and a
user part with no password is redacted when it is shaped like a token. A
plain user name, a port and a placeholder stay as written. Every token-shaped
value is built at run time."""
from __future__ import annotations

import pytest

from canon.workspace.scrub import find_secrets, scrub

V = "canaryV4lue" + "Q7x9"


@pytest.mark.parametrize("text, secret", [
    ("https://" + V + "@github.com/o/r.git", V),
    ("https://aB3" + "dE5fG@host.example/x", "aB3dE5fG"),
    ("https://" + "9f8e7d6c5b4a3210" * 2 + "@github.com/o/r", "9f8e7d6c5b4a3210"),
    ("https://deploy:" + "pw" + "@host.example/x", ":pw@"),
    ("ssh://git:" + "hunter" + "@host.example/o/r", "hunter"),
    ("https://oauth2:" + V + "@gitlab.com/o/r.git", V),
])
def test_a_token_or_a_password_in_a_url_user_part_is_redacted(text, secret):
    result = scrub(text)
    assert result.hits.get("connection-string") == 1, text
    assert secret not in result.text
    assert find_secrets(result.text) == []


@pytest.mark.parametrize("text", [
    "ssh://git@github.com/o/r.git",
    "https://first.last@example.com/repo",
    "https://github-actions-bot@github.com/o/r",
    "https://x-access-token@github.com/o/r",
    "https://user123@host.example/x",
    "https://registry.npmjs.org:443/@scope/pkg",
    "https://${GITHUB_TOKEN}@github.com/o/r",
    "https://deploy:<password>@host.example/x",
])
def test_a_plain_user_name_a_port_and_a_placeholder_stay(text):
    assert find_secrets(text) == [], text
    assert scrub(text).text == text
