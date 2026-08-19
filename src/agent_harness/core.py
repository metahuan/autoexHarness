from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Iterable, Mapping


class Phase(str, Enum):
    PLAN = "PLAN"
    DO = "DO"
    CHECK = "CHECK"
    ACT = "ACT"


@dataclass(frozen=True)
class ActionContract:
    action: str
    required_fields: tuple[str, ...] = ()
    allowed_phases: tuple[Phase, ...] = (Phase.DO,)
    requires_evidence: bool = False


@dataclass(frozen=True)
class ActionRequest:
    action: str
    phase: Phase
    payload: Mapping[str, Any]
    evidence: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class Decision:
    allowed: bool
    code: str
    reasons: tuple[str, ...]
    receipt_id: str
    normalized_payload: Mapping[str, Any] = field(default_factory=dict)


class HarnessGate:
    """Fail-closed gate placed immediately before a tool adapter."""

    def __init__(self, contracts: Iterable[ActionContract]) -> None:
        self._contracts = {contract.action: contract for contract in contracts}

    def authorize(self, request: ActionRequest) -> Decision:
        contract = self._contracts.get(request.action)
        if contract is None:
            return self._decision(request, False, "unknown_action", (f"unknown action: {request.action}",))

        reasons: list[str] = []
        if request.phase not in contract.allowed_phases:
            allowed = ", ".join(phase.value for phase in contract.allowed_phases)
            reasons.append(f"action requires phase: {allowed}")

        for field_name in contract.required_fields:
            value = request.payload.get(field_name)
            if value is None or value == "":
                reasons.append(f"missing required field: {field_name}")

        if contract.requires_evidence and not request.evidence:
            reasons.append("evidence is required")

        if reasons:
            return self._decision(request, False, "contract_violation", tuple(reasons))

        normalized = {key: request.payload[key] for key in sorted(request.payload)}
        return self._decision(request, True, "allowed", (), normalized)

    @staticmethod
    def _decision(
        request: ActionRequest,
        allowed: bool,
        code: str,
        reasons: tuple[str, ...],
        normalized_payload: Mapping[str, Any] | None = None,
    ) -> Decision:
        receipt_source = json.dumps(
            {
                "action": request.action,
                "phase": request.phase.value,
                "payload": dict(request.payload),
                "evidence": list(request.evidence),
                "allowed": allowed,
                "code": code,
                "reasons": reasons,
            },
            ensure_ascii=True,
            sort_keys=True,
            default=str,
        )
        receipt_id = "rcpt_" + sha256(receipt_source.encode("utf-8")).hexdigest()[:16]
        return Decision(allowed, code, reasons, receipt_id, normalized_payload or {})


class StateTransitionError(RuntimeError):
    pass


class PDCAMachine:
    """Sequential PDCA machine. Skipped or unproven transitions are rejected."""

    _NEXT = {
        Phase.PLAN: Phase.DO,
        Phase.DO: Phase.CHECK,
        Phase.CHECK: Phase.ACT,
        Phase.ACT: Phase.PLAN,
    }
    _PROOF = {
        (Phase.PLAN, Phase.DO): "plan_id",
        (Phase.DO, Phase.CHECK): "execution_receipt",
        (Phase.CHECK, Phase.ACT): "check_result",
        (Phase.ACT, Phase.PLAN): "retrospective",
    }

    def __init__(self, initial: Phase = Phase.PLAN) -> None:
        self.phase = initial

    def advance(self, target: Phase, proof: Mapping[str, Any]) -> Phase:
        expected = self._NEXT[self.phase]
        if target is not expected:
            raise StateTransitionError(
                f"cannot transition from {self.phase.value} to {target.value}; expected {expected.value}"
            )

        proof_key = self._PROOF[(self.phase, target)]
        if proof.get(proof_key) in (None, "", False):
            raise StateTransitionError(
                f"transition from {self.phase.value} to {target.value} requires proof: {proof_key}"
            )

        self.phase = target
        return self.phase
