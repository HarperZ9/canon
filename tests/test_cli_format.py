from __future__ import annotations

import io
from collections.abc import Iterator, Mapping

import pytest

from canon.exit_codes import EX_INTERNAL, EX_OK


def test_write_result_json_emits_canonical_envelope_with_one_stdout_lf() -> None:
    from canon.cli_format import make_result, write_result

    result = make_result(
        ok=True,
        command="doctor",
        failure_code="ok",
        message="ready",
        data={"z": 2, "a": 1},
    )
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = write_result(result, stdout=stdout, stderr=stderr, json_output=True, color=True)

    assert exit_code == EX_OK
    assert stdout.getvalue() == (
        '{"command":"doctor","data":{"a":1,"z":2},"exit_code":0,'
        '"failure_code":"ok","message":"ready","ok":true}\n'
    )
    assert stderr.getvalue() == ""


def test_json_write_to_text_wrapper_uses_utf8_bytes_without_newline_translation() -> None:
    from canon.cli_format import make_result, write_result

    result = make_result(
        ok=True,
        command="doctor",
        failure_code="ok",
        message="ready",
        data={"word": "café"},
    )
    buffer = io.BytesIO()
    stdout = io.TextIOWrapper(buffer, encoding="utf-16", newline="\r\n")

    exit_code = write_result(result, stdout=stdout, stderr=io.StringIO(), json_output=True, color=False)
    stdout.flush()

    assert exit_code == EX_OK
    assert buffer.getvalue() == (
        '{"command":"doctor","data":{"word":"café"},"exit_code":0,'
        '"failure_code":"ok","message":"ready","ok":true}\n'
    ).encode("utf-8")


def test_make_result_snapshots_nested_data_before_caller_mutation() -> None:
    from canon.cli_format import make_result, write_result

    data = {"items": ["first"], "nested": {"count": 1}}
    result = make_result(ok=True, command="doctor", failure_code="ok", message="ready", data=data)

    data["items"].append("second")  # type: ignore[attr-defined]
    data["nested"]["count"] = 2  # type: ignore[index]
    stdout = io.StringIO()

    write_result(result, stdout=stdout, stderr=io.StringIO(), json_output=True, color=False)

    assert stdout.getvalue() == (
        '{"command":"doctor","data":{"items":["first"],"nested":{"count":1}},'
        '"exit_code":0,"failure_code":"ok","message":"ready","ok":true}\n'
    )


def test_result_data_is_recursively_immutable_and_serializes_from_frozen_snapshot() -> None:
    from canon.cli_format import make_result, write_result

    result = make_result(
        ok=True,
        command="doctor",
        failure_code="ok",
        message="ready",
        data={"items": [{"count": 1}]},
    )

    assert result.data is not None
    with pytest.raises(TypeError):
        result.data["items"] = []  # type: ignore[index]
    items = result.data["items"]
    assert isinstance(items, tuple)
    with pytest.raises(TypeError):
        items[0]["count"] = 2  # type: ignore[index]

    stdout = io.StringIO()
    write_result(result, stdout=stdout, stderr=io.StringIO(), json_output=True, color=False)

    assert stdout.getvalue() == (
        '{"command":"doctor","data":{"items":[{"count":1}]},"exit_code":0,'
        '"failure_code":"ok","message":"ready","ok":true}\n'
    )


def test_unknown_failure_codes_fail_closed_but_success_requires_ok_code() -> None:
    from canon.cli_format import make_result

    failure = make_result(ok=False, command="doctor", failure_code="future-code", message="blocked")

    with pytest.raises(TypeError, match="invalid CLI result"):
        make_result(ok=True, command="doctor", failure_code="future-code", message="ready")
    assert failure.exit_code == EX_INTERNAL
    assert failure.failure_code == "future-code"


def test_factory_rejects_failure_with_ok_code() -> None:
    from canon.cli_format import make_result

    with pytest.raises(TypeError) as excinfo:
        make_result(ok=False, command="doctor", failure_code="ok", message="blocked")

    assert str(excinfo.value) == "invalid CLI result"


def test_direct_result_construction_and_write_validation_reject_inconsistent_invariants() -> None:
    from canon.cli_format import CliResult, make_result, write_result

    with pytest.raises(TypeError) as direct_exc:
        CliResult(
            ok=True,
            command="doctor",
            failure_code="conflict",
            message="ready",
            data=None,
            exit_code=5,
        )

    tampered = make_result(ok=True, command="doctor", failure_code="ok", message="ready")
    object.__setattr__(tampered, "exit_code", 2)
    with pytest.raises(TypeError) as write_exc:
        write_result(tampered, stdout=io.StringIO(), stderr=io.StringIO(), json_output=True, color=False)

    assert str(direct_exc.value) == "invalid CLI result"
    assert str(write_exc.value) == "invalid CLI result"


class _HostileMapping(Mapping[object, object]):
    def __getitem__(self, key: object) -> object:
        del key
        return "value"

    def __iter__(self) -> Iterator[object]:
        return iter([object()])

    def __len__(self) -> int:
        return 1

    def __repr__(self) -> str:
        return "leaked-secret-token"


def test_invalid_result_data_fails_closed_without_hostile_repr() -> None:
    from canon.cli_format import make_result

    with pytest.raises(TypeError) as excinfo:
        make_result(
            ok=True,
            command="doctor",
            failure_code="ok",
            message="ready",
            data=_HostileMapping(),
        )

    message = str(excinfo.value)
    assert "invalid result data" in message
    assert "leaked-secret-token" not in message
