# Agent Harness

> Agent thinks. Harness decides whether it may act.

Agent Harness is a fail-closed control layer for ordinary AI agents. It sits between model output and tool execution, so an agent cannot turn an invalid structure, an unsupported claim, or an out-of-order plan into a real-world action.

中文主页：[www.changzhiai.com/harness](https://www.changzhiai.com/harness?utm_source=github&utm_medium=referral&utm_campaign=agent_harness&utm_content=readme_top)

GitHub 仓库：[metahuan/autoexHarness](https://github.com/metahuan/autoexHarness)

Releases：[查看版本发布](https://github.com/metahuan/autoexHarness/releases)

## Why agents need a Harness

Most agent frameworks optimize for making the next tool call. Production systems also need an independent component that can say no.

1. **Wrong structure, no execution.** Every action must satisfy an explicit contract. Missing fields, invalid values, unknown actions, and permission violations are denied before a tool is touched.
2. **Stop execution hallucinations before execution.** A model may form a hypothesis, but it may not present that hypothesis as verified input to a tool. Evidence-required actions stay blocked until evidence is attached and validated.
3. **PDCA is a state machine, not a suggestion.** PLAN, DO, CHECK, and ACT must happen in order. The agent cannot skip CHECK, repeat DO without review, or jump ahead because a prompt asked it to.

The goal is not to eliminate every incorrect sentence a model can generate. The goal is to prevent detectable, unsupported model output from becoming an irreversible action.

## The execution boundary

```text
user / event
     |
     v
AI Agent proposes intent + payload
     |
     v
Agent Harness
  - action contract
  - evidence gate
  - permission policy
  - PDCA state machine
  - decision receipt
     |
     +-- DENY -> structured reason, no tool call
     |
     `-- ALLOW -> action gateway -> tool
```

## Reference implementation

The code in this directory is a dependency-free reference implementation of the public protocol. It is intentionally small: it demonstrates the control boundary, not a complete production runtime.

```bash
python -m pip install -e .
python examples/minimal_gate.py
python -m unittest discover -s tests
```

```python
from agent_harness import ActionContract, ActionRequest, HarnessGate, Phase

gate = HarnessGate([
    ActionContract(
        action="update_listing",
        required_fields=("listing_id", "price", "currency"),
        allowed_phases=(Phase.DO,),
        requires_evidence=True,
    )
])

decision = gate.authorize(ActionRequest(
    action="update_listing",
    phase=Phase.DO,
    payload={"listing_id": "SKU-1", "price": 19.9},
    evidence=(),
))

assert decision.allowed is False
assert decision.code == "contract_violation"
```

## Public protocol

An implementation is compatible when it preserves these invariants:

- Default decision is deny.
- Unknown actions never reach a tool.
- Contract validation happens before execution.
- Evidence-required actions cannot self-certify with model text alone.
- State transitions are explicit and sequential.
- Every allow or deny decision produces a machine-readable receipt.
- Tool adapters receive only normalized, authorized payloads.

## Repository roadmap

- `v0.1`: contracts, evidence gate, PDCA machine, decision receipts.
- `v0.2`: policy packs and adapter protocol.
- `v0.3`: framework integrations and trace viewer.
- `v1.0`: stable protocol, compatibility suite, security documentation.

The public landing page contains the product narrative and integration direction: [changzhiai.com/harness](https://www.changzhiai.com/harness?utm_source=github&utm_medium=referral&utm_campaign=agent_harness&utm_content=readme_protocol).

For a managed business runtime built around governed execution, visit [畅智 AI](https://www.changzhiai.com/account?utm_source=github&utm_medium=referral&utm_campaign=agent_harness&utm_content=readme_bottom).

## License

This GitHub repository is currently published under the MIT License. See [`LICENSE`](./LICENSE) for the complete terms. Before extracting additional runtime code from the private product, complete the dependency, copyright, secret, and trademark audit described in the implementation plan.
