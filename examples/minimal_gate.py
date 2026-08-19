from agent_harness import ActionContract, ActionRequest, HarnessGate, PDCAMachine, Phase


gate = HarnessGate(
    [
        ActionContract(
            action="update_listing",
            required_fields=("listing_id", "price", "currency"),
            allowed_phases=(Phase.DO,),
            requires_evidence=True,
        )
    ]
)

blocked = gate.authorize(
    ActionRequest(
        action="update_listing",
        phase=Phase.DO,
        payload={"listing_id": "SKU-1", "price": 19.9},
    )
)
print(blocked)

machine = PDCAMachine()
machine.advance(Phase.DO, {"plan_id": "plan-001"})

allowed = gate.authorize(
    ActionRequest(
        action="update_listing",
        phase=machine.phase,
        payload={"listing_id": "SKU-1", "price": 19.9, "currency": "USD"},
        evidence=({"source": "erp", "observed_at": "2026-08-19T09:00:00Z"},),
    )
)
print(allowed)
