from __future__ import annotations


def test_exit_code_constants_are_stable() -> None:
    from canon.exit_codes import (
        EX_BUDGET,
        EX_CONFLICT,
        EX_GATE,
        EX_INTERNAL,
        EX_IO,
        EX_OK,
        EX_SECURITY,
        EX_UNAVAILABLE,
        EX_UNSUPPORTED,
        EX_USAGE,
    )

    assert EX_OK == 0
    assert EX_GATE == 1
    assert EX_USAGE == 2
    assert EX_UNAVAILABLE == 3
    assert EX_SECURITY == 4
    assert EX_CONFLICT == 5
    assert EX_BUDGET == 6
    assert EX_UNSUPPORTED == 7
    assert EX_IO == 8
    assert EX_INTERNAL == 70


def test_failure_codes_map_to_stable_process_exit_codes() -> None:
    from canon.exit_codes import exit_code_for

    assert exit_code_for("ok") == 0
    assert exit_code_for("readiness_failed") == 1
    assert exit_code_for("source_changed") == 1
    assert exit_code_for("invalid_args") == 2
    assert exit_code_for("source_unreachable") == 3
    assert exit_code_for("secret_quarantine") == 4
    assert exit_code_for("conflict") == 5
    assert exit_code_for("critical_atom_loss") == 6
    assert exit_code_for("tier_mislabeled") == 7
    assert exit_code_for("io_error") == 8
    assert exit_code_for("future-code") == 70
