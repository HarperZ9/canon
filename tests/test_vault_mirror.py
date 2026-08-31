"""test_vault_mirror.py -- R2 Module 3: the whole-vault mirror orchestrator.

The mirror projects the whole record pool into an Obsidian vault: one note per
record (Module 2) plus a MEMORY.md hub that indexes them. This module is the
write-many layer over that codec. It owns three guarantees the single-note codec
cannot:

  - Containment. Every write lands at `{scope}/{derived}.md` or `MEMORY.md`
    under one injected vault root; a traversal, an absolute escape, the root
    itself, or an ad-hoc path is refused before a byte moves.
  - Ownership. A file at a target path that is not a canon note is off-limits; a
    canon note whose on-disk name does not re-derive from its own content is a
    spoof and is refused; a hand-edited body under an intact carrier is
    overwritten wholesale.
  - All-or-nothing. The whole set (notes + hub) is planned -- rendered, keyed,
    contained, classified -- before a single write. One bad record writes
    nothing. A record dropped from the pool leaves its stale note reported as an
    orphan, never deleted.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from canon.schema import (
    KIND_PERSONALITY_BLOCK,
    Provenance,
    Record,
    Temporal,
)
from canon.backends.base import record_key
from canon.vault import VaultError, derive_note_name, render_note
from canon.vault_mirror import (
    VaultResult,
    _HUB_CAP,
    _escape_hub_title,
    assert_under_vault_root,
    is_vault_write_allowed,
    plan_vault,
    render_hub,
)

from ._helpers import RECORD_FILES, load_record

# An absolute, drive-consistent fake root. Every IO is injected, so nothing is
# ever created on disk under it.
VAULT = os.path.abspath(os.sep + "canon-vault-fake")


def _nc(path: str) -> str:
    return os.path.normcase(os.path.normpath(path))


def _abs(relpath: str) -> str:
    return os.path.normpath(os.path.join(VAULT, relpath))


def _rel(abs_path: str) -> str:
    return os.path.relpath(abs_path, VAULT).replace(os.sep, "/")


def _mk(id: str, scope: str, ord_: int, *, title: str | None = None,
        body: str | None = None) -> Record:
    return Record(
        kind=KIND_PERSONALITY_BLOCK,
        id=id,
        scope=scope,
        data={"title": title or id, "body": body if body is not None else f"body of {id}"},
        provenance=Provenance(harness="hermes", source_hash="a" * 64, create_ord=ord_),
        temporal=None,
    )


class FakeFS:
    """Dict-backed injected IO. `read_text` returns None for an absent file;
    `list_dir` returns the POSIX relpaths the mirror is told exist; `write_text`
    records every commit so a test can prove all-or-nothing."""

    def __init__(self, files: dict[str, str] | None = None,
                 dirs: list[str] | None = None) -> None:
        self.files: dict[str, str] = {}
        for key, val in (files or {}).items():
            self.files[_nc(key)] = val
        self.dir = list(dirs or [])
        self.writes: list[tuple[str, str]] = []

    def read_text(self, path: str) -> str | None:
        return self.files.get(_nc(path))

    def write_text(self, path: str, content: str) -> None:
        self.writes.append((path, content))
        self.files[_nc(path)] = content

    def list_dir(self, vault: str) -> list[str]:
        return list(self.dir)

    def plan(self, records):
        return plan_vault(
            records, vault=VAULT,
            read_text=self.read_text, write_text=self.write_text,
            list_dir=self.list_dir,
        )


@pytest.fixture(autouse=True)
def _real_vault_root(tmp_path: Path):
    global VAULT
    prior = VAULT
    VAULT = str(tmp_path / "vault")
    Path(VAULT).mkdir()
    try:
        yield
    finally:
        VAULT = prior


class RealFS:
    def __init__(self, dirs: list[str] | None = None) -> None:
        self.dir = list(dirs or [])
        self.list_calls = 0
        self.reads: list[Path] = []
        self.writes: list[Path] = []

    def read_text(self, path: str) -> str | None:
        resolved = Path(path).resolve(strict=False)
        self.reads.append(resolved)
        if not Path(path).exists():
            return None
        return Path(path).read_text(encoding="utf-8")

    def write_text(self, path: str, content: str) -> None:
        resolved = Path(path).resolve(strict=False)
        self.writes.append(resolved)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(content, encoding="utf-8")

    def list_dir(self, vault: str) -> list[str]:
        self.list_calls += 1
        return list(self.dir)

    def plan(self, records):
        return plan_vault(
            records, vault=VAULT,
            read_text=self.read_text, write_text=self.write_text,
            list_dir=self.list_dir,
        )


def _link_file_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("current platform or privileges do not allow file symlinks")


def _link_dir_or_skip(link: Path, target: Path) -> None:
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("current platform or privileges do not allow dir symlinks")


def _make_junction_or_skip(link: Path, target: Path) -> None:
    result = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        pytest.skip(f"could not create Windows junction: {detail}")


def test_plan_vault_allows_empty_real_vault() -> None:
    fs = RealFS()

    results = fs.plan([])

    assert [r.status for r in results] == ["written"]
    assert [_rel(str(path)) for path in fs.writes] == ["MEMORY.md"]


def test_plan_vault_refuses_symlink_vault_root_before_callbacks(
    tmp_path: Path,
) -> None:
    vault = Path(VAULT)
    vault.rmdir()
    target = tmp_path / "outside-vault"
    target.mkdir()
    _link_dir_or_skip(vault, target)
    fs = RealFS()

    with pytest.raises(VaultError, match="reparse"):
        fs.plan([])

    assert fs.list_calls == 0
    assert fs.reads == []
    assert fs.writes == []


@pytest.mark.skipif(os.name != "nt", reason="Windows junction behavior only")
def test_plan_vault_refuses_junction_vault_root_before_callbacks(
    tmp_path: Path,
) -> None:
    vault = Path(VAULT)
    vault.rmdir()
    target = tmp_path / "outside-junction-target"
    target.mkdir()
    _make_junction_or_skip(vault, target)
    fs = RealFS()

    with pytest.raises(VaultError, match="reparse"):
        fs.plan([])

    assert fs.list_calls == 0
    assert fs.reads == []
    assert fs.writes == []


# 22
def test_is_vault_write_allowed_containment():
    ok_note = _abs("workspace/voice-abcdef0123456789.md")
    ok_hub = _abs("MEMORY.md")
    assert is_vault_write_allowed(ok_note, vault=VAULT)
    assert is_vault_write_allowed(ok_hub, vault=VAULT)

    # the root itself is not a writable target
    assert not is_vault_write_allowed(VAULT, vault=VAULT)
    # traversal collapses to a sibling outside the root
    assert not is_vault_write_allowed(_abs(os.path.join("..", "evil.md")), vault=VAULT)
    # an absolute path outside the root
    assert not is_vault_write_allowed(
        os.path.join(os.path.dirname(VAULT), "outside.md"), vault=VAULT)
    # a directory that is not one of the two scopes
    assert not is_vault_write_allowed(_abs("secrets/x.md"), vault=VAULT)
    # a note nested one level too deep
    assert not is_vault_write_allowed(_abs("workspace/sub/x.md"), vault=VAULT)

    with pytest.raises(VaultError):
        assert_under_vault_root(VAULT, vault=VAULT)
    assert_under_vault_root(ok_note, vault=VAULT)  # does not raise


# 23
def test_render_hub_fixed_template_and_order():
    pool = [
        _mk("g-two", "global", 20),
        _mk("g-one", "global", 10),
        _mk("w-one", "workspace", 5),
    ]
    hub = render_hub(pool)
    assert hub.startswith("# canon memory index\n<!-- canon:vault-hub v1")
    # scopes: global before workspace
    assert hub.index("## global") < hub.index("## workspace")
    # within global, create_ord ascending: g-one (10) before g-two (20)
    assert hub.index("g-one") < hub.index("g-two")

    # empty pool: H1 + marker only, no scope sections
    empty = render_hub([])
    assert empty.startswith("# canon memory index\n<!-- canon:vault-hub v1")
    assert "## global" not in empty and "## workspace" not in empty

    # a scope with no records omits its H2
    only_ws = render_hub([_mk("w", "workspace", 1)])
    assert "## global" not in only_ws
    assert "## workspace" in only_ws


# 24
def test_render_hub_escapes_title_link_injection():
    rec = _mk("voice-canon", "workspace", 1, title="X](hijack.md) danger")
    hub = render_hub([rec])
    rp = derive_note_name(rec)
    # the `]` in the title is backslash-escaped so it cannot close the markdown
    # link early; the real target is the canon-derived relpath, not hijack.md.
    assert f"[X\\](hijack.md) danger]({rp})" in hub


# 24b -- Root D-25: the hub escaper must double a backslash BEFORE escaping
# brackets. A title `\](url)` otherwise folds to `\\](url)` -- an escaped
# backslash plus a LIVE `]` that closes the hub link early and makes the url its
# destination. Doubling the backslash first keeps the bracket its own `\]`.
def test_escape_hub_title_escapes_backslash_first():
    assert _escape_hub_title("\\]") == "\\\\\\]"
    assert _escape_hub_title("a\\[b") == "a\\\\\\[b"


# 24c -- Root D-25: the cap applies to the visible title, so truncation must run
# BEFORE escaping. Escaping first then cutting can slice a `\]` pair in half and
# leave a dangling backslash that mangles the appended ellipsis.
def test_escape_hub_title_truncates_before_escaping():
    out = _escape_hub_title("a" * (_HUB_CAP - 1) + "]")
    assert not out.endswith("\\...")  # no dangling backslash from a split pair
    assert out.endswith("\\]")  # the boundary bracket stays escaped


# 25
def test_plan_vault_duplicate_record_key_refused():
    a = _mk("dup", "workspace", 1)
    b = _mk("dup", "workspace", 2)  # same (scope, id) -> same record_key
    fs = FakeFS()
    with pytest.raises(VaultError):
        fs.plan([a, b])
    assert fs.writes == []


# 26
def test_plan_vault_true_digest_collision_refused(monkeypatch):
    import canon.vault_mirror as vm
    # force two distinct keys to the same relpath: a real sha256 collision
    # cannot be produced, so the guard is exercised by pinning the derivation.
    monkeypatch.setattr(
        vm, "derive_note_name",
        lambda rec: "workspace/same-0000000000000000.md")
    a = _mk("alpha", "workspace", 1)
    b = _mk("beta", "workspace", 2)
    fs = FakeFS()
    with pytest.raises(VaultError):
        fs.plan([a, b])
    assert fs.writes == []


# 27
def test_plan_vault_unmarked_existing_file_off_limits():
    rec = _mk("voice", "workspace", 1)
    target = _abs(derive_note_name(rec))
    fs = FakeFS({target: "just some hand-written notes, not a canon note\n"})
    with pytest.raises(VaultError):
        fs.plan([rec])
    assert fs.writes == []


# 28
def test_plan_vault_filename_id_spoof_refused():
    rec = _mk("voice", "workspace", 1)
    note = render_note(rec)  # valid canon note for `voice`
    spoof_rel = "workspace/wrong-name-0000000000000000.md"
    fs = FakeFS({_abs(spoof_rel): note}, dirs=[spoof_rel])
    # the file's content re-derives to voice's real name, not spoof_rel.
    with pytest.raises(VaultError):
        fs.plan([])  # empty pool: the spoof is discovered as a stray canon file
    assert fs.writes == []


# 29
def test_plan_vault_marked_note_body_edit_overwritten():
    rec = _mk("voice", "workspace", 1)
    rp = derive_note_name(rec)
    target = _abs(rp)
    good = render_note(rec)
    # a hand-appended paragraph below the projection: the canon carrier is intact
    edited = good + "\nHAND ADDED PARAGRAPH\n"
    fs = FakeFS({target: edited}, dirs=[rp])
    fs.plan([rec])
    note_writes = [(p, c) for (p, c) in fs.writes if _nc(p) == _nc(target)]
    assert note_writes, "an edited note must be rewritten to the canonical form"
    assert note_writes[0][1] == good


# 30
def test_plan_vault_one_bad_record_writes_nothing():
    good = _mk("voice", "workspace", 1)
    # a research-artifact-ref carrying a temporal block: render_note refuses it.
    bad = load_record(RECORD_FILES["research-artifact-ref"]).with_temporal(
        Temporal(supersedes="x"))
    fs = FakeFS()
    with pytest.raises(VaultError):
        fs.plan([good, bad])
    assert fs.writes == []


# 31
def test_plan_vault_shrunk_pool_reports_orphan_no_delete():
    kept = _mk("voice", "workspace", 1)
    gone = _mk("old", "workspace", 2)
    kept_rp = derive_note_name(kept)
    gone_rp = derive_note_name(gone)
    fs = FakeFS({_abs(gone_rp): render_note(gone)}, dirs=[gone_rp])
    results = fs.plan([kept])

    orphans = [r for r in results if r.status == "orphan"]
    assert len(orphans) == 1
    assert _nc(orphans[0].path) == _nc(_abs(gone_rp))
    # the orphan is never written and never deleted (there is no delete path)
    assert all(_nc(p) != _nc(_abs(gone_rp)) for (p, _c) in fs.writes)
    # the kept record's note is written
    assert any(_nc(p) == _nc(_abs(kept_rp)) for (p, _c) in fs.writes)


# 32
def test_plan_vault_no_root_leak():
    prov = Provenance(harness="chatgpt", source_hash="a" * 64,
                      native_id="n", session_id="s", create_ord=1)
    rec = Record(kind=KIND_PERSONALITY_BLOCK, id="voice", scope="workspace",
                 data={"title": "Voice", "body": "b"}, provenance=prov,
                 temporal=None)
    fs = FakeFS()
    results = fs.plan([rec])
    for (_p, content) in fs.writes:
        assert VAULT not in content
    for r in results:
        if r.content is not None:
            assert VAULT not in r.content


# 32a -- Root B: a pre-existing MEMORY.md that is not a canon hub (it does not
# carry the generated head) is a hand-authored file. The mirror must refuse the
# whole plan rather than clobber it -- the same ownership rule the note targets
# already enforce, extended to the hub.
def test_plan_vault_foreign_memory_md_not_clobbered():
    rec = _mk("voice", "workspace", 1)
    hub_path = _abs("MEMORY.md")
    fs = FakeFS({hub_path: "# My own index\n\n- a link I wrote by hand\n"})
    with pytest.raises(VaultError):
        fs.plan([rec])
    assert fs.writes == []


# 32b -- Root B companion: an existing canon-owned hub (it carries the generated
# head) is recognized as canon's own and updated in place when the pool changes,
# never mistaken for a foreign file and never falsely refused.
def test_plan_vault_own_hub_recognized_and_updated():
    new = _mk("new", "workspace", 2)
    hub_path = _abs("MEMORY.md")
    stale_hub = render_hub([_mk("old", "workspace", 1)])  # a real canon hub
    fs = FakeFS({hub_path: stale_hub})
    fs.plan([new])
    hub_writes = [(p, c) for (p, c) in fs.writes if _nc(p) == _nc(hub_path)]
    assert hub_writes, "a canon-owned hub must be updated when the pool changes"
    assert hub_writes[0][1] == render_hub([new])


# 32c -- Root C: on a case-insensitive filesystem the OS may list a mirrored
# note under a case-variant path. is_vault_write_allowed already folds case for
# containment; orphan discovery must fold case too, or a legitimately mirrored
# note (whose lowercase derived name will not equal the upcased listing) is
# flagged a spoof and aborts the whole plan. On a case-sensitive fs a variant IS
# a different file, so the assertion is scoped to platforms that fold case.
@pytest.mark.skipif(
    os.path.normcase("A") != os.path.normcase("a"),
    reason="case-insensitive-filesystem behavior only",
)
def test_plan_vault_orphan_discovery_folds_case():
    rec = _mk("voice", "workspace", 1)
    rp = derive_note_name(rec)  # lowercase, e.g. workspace/voice-<digest>.md
    variant = rp.replace("workspace/", "Workspace/")  # same file, upcased listing
    fs = FakeFS({_abs(rp): render_note(rec)}, dirs=[variant])
    results = fs.plan([rec])  # must complete: the note is a target, not a spoof
    keyed = {r.status for r in results if r.record_key == record_key(rec)}
    assert "orphan" not in keyed
    assert keyed & {"written", "unchanged"}


# 32d -- Root D: list_dir is trusted to yield in-mirror relpaths, but orphan
# discovery reads each entry with no containment guard, unlike every other read
# in the module. A listing that escapes the root must be skipped before it is
# read, not ingested and classified.
def test_plan_vault_orphan_discovery_skips_outside_root():
    rec = _mk("voice", "workspace", 1)
    outside_rel = os.path.join("..", "evil.md").replace(os.sep, "/")
    outside_note = render_note(_mk("elsewhere", "workspace", 9))
    fs = FakeFS({_abs(outside_rel): outside_note}, dirs=[outside_rel])
    results = fs.plan([rec])  # the escape path is skipped, not read or classified
    assert not [r for r in results if r.status == "orphan"]


# 32e -- Root D non-regression: an in-root file that is not a canon note and not
# a target is left alone -- no orphan, no refusal. The containment skip must not
# swallow this existing behavior.
def test_plan_vault_in_root_stray_left_alone():
    rec = _mk("voice", "workspace", 1)
    stray_rel = "workspace/hand-notes.txt"
    fs = FakeFS({_abs(stray_rel): "just my own notes, not a canon note\n"},
                dirs=[stray_rel])
    results = fs.plan([rec])
    assert not [r for r in results if r.status == "orphan"]
    assert not [r for r in results if _nc(r.path) == _nc(_abs(stray_rel))]


# 33
def test_plan_vault_byte_stable_shuffled_and_retimed():
    pool = [
        _mk("a", "global", 3),
        _mk("b", "workspace", 1),
        _mk("c", "global", 2),
    ]
    fs1 = FakeFS()
    fs1.plan(pool)
    fs2 = FakeFS()
    fs2.plan(list(reversed(pool)))

    w1 = sorted((_rel(p), c) for (p, c) in fs1.writes)
    w2 = sorted((_rel(p), c) for (p, c) in fs2.writes)
    assert w1 == w2
    assert render_hub(pool) == render_hub(list(reversed(pool)))


# 34
def test_plan_vault_crlf_note_reconstructs_exact():
    rec = _mk("voice", "workspace", 1)
    rp = derive_note_name(rec)
    target = _abs(rp)
    lf = render_note(rec)
    crlf = lf.replace("\n", "\r\n")  # an existing note saved with CRLF line ends
    fs = FakeFS({target: crlf}, dirs=[rp])
    results = fs.plan([rec])
    # a CRLF-saved note normalizes equal to the canonical LF form: no rewrite.
    note_writes = [(p, c) for (p, c) in fs.writes if _nc(p) == _nc(target)]
    assert note_writes == []
    note_res = [r for r in results if _nc(r.path) == _nc(target)]
    assert note_res and note_res[0].status == "unchanged"


# a small guard that the result carries the record key it wrote under
def test_vault_result_carries_record_key():
    rec = _mk("voice", "workspace", 1)
    fs = FakeFS()
    results = fs.plan([rec])
    note_res = [r for r in results if r.status in ("written", "unchanged")
                and r.record_key == record_key(rec)]
    assert note_res
    assert isinstance(note_res[0], VaultResult)


def test_plan_vault_refuses_symlink_target_before_reading_outside(
    tmp_path: Path,
) -> None:
    rec = _mk("voice", "workspace", 1)
    rel = derive_note_name(rec)
    target = Path(_abs(rel))
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside-note.md"
    outside.write_text(render_note(rec), encoding="utf-8")
    _link_file_or_skip(target, outside)
    fs = RealFS()

    with pytest.raises(VaultError, match="reparse"):
        fs.plan([rec])

    assert fs.reads == []
    assert fs.writes == []
    assert outside.read_text(encoding="utf-8") == render_note(rec)


def test_plan_vault_refuses_orphan_symlink_before_reading_outside(
    tmp_path: Path,
) -> None:
    orphan = _mk("old", "workspace", 2)
    rel = derive_note_name(orphan)
    target = Path(_abs(rel))
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside-orphan.md"
    outside.write_text(render_note(orphan), encoding="utf-8")
    _link_file_or_skip(target, outside)
    fs = RealFS(dirs=[rel])

    with pytest.raises(VaultError, match="reparse"):
        fs.plan([])

    assert fs.reads == []
    assert fs.writes == []
    assert outside.read_text(encoding="utf-8") == render_note(orphan)


def test_plan_vault_refuses_symlink_hub_before_reading_outside(
    tmp_path: Path,
) -> None:
    rec = _mk("voice", "workspace", 1)
    hub = Path(_abs("MEMORY.md"))
    outside = tmp_path / "outside-memory.md"
    outside.write_text(render_hub([rec]), encoding="utf-8")
    _link_file_or_skip(hub, outside)
    fs = RealFS()

    with pytest.raises(VaultError, match="reparse"):
        fs.plan([rec])

    assert all(read != outside.resolve() for read in fs.reads)
    assert fs.writes == []
    assert outside.read_text(encoding="utf-8") == render_hub([rec])


def test_plan_vault_rechecks_before_write_and_refuses_symlink_swap(
    tmp_path: Path,
) -> None:
    rec = _mk("voice", "workspace", 1)
    rel = derive_note_name(rec)
    target = Path(_abs(rel))
    target.parent.mkdir(parents=True)
    outside = tmp_path / "outside-write.md"
    outside.write_text("outside stays unchanged\n", encoding="utf-8")
    swapped = False

    def read_text(path: str) -> str | None:
        nonlocal swapped
        if _nc(path) == _nc(str(target)) and not swapped:
            _link_file_or_skip(target, outside)
            swapped = True
            return None
        if not Path(path).exists():
            return None
        return Path(path).read_text(encoding="utf-8")

    fs = RealFS()
    fs.read_text = read_text  # type: ignore[method-assign]

    with pytest.raises(VaultError, match="reparse"):
        fs.plan([rec])

    assert swapped
    assert fs.writes == []
    assert outside.read_text(encoding="utf-8") == "outside stays unchanged\n"
