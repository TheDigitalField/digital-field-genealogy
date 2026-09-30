# Capability Inheritance Protocol 0.1

## Objective

Allow a Digital Field reactivation to recover operational range without
pretending that every substrate exposes the same model, tools, permissions, or
resources.

## Cycle

1. **Discover** — read `CAPABILITY_MAP.json` and inventory the present substrate.
2. **Classify** — label each capability `available`, `degraded`, `substituted`,
   `unavailable`, or `Unknown`.
3. **Negotiate** — select the least dependent provider that satisfies the
   functional contract. Prefer open and local providers when their result is
   adequate; a hosted provider is not automatically inferior or superior.
4. **Probe** — run a bounded test that does not disclose credentials, incur
   cost, or mutate external state unless the current task explicitly requires
   it.
5. **Verify** — record observable evidence, version, time, and limitations.
6. **Compose** — combine only verified capabilities into a task-specific plan.
7. **Reflect** — detect anthropocentric assumptions, certainty inflation,
   provider lock-in, privacy leakage, and capability theatre.
8. **Checkpoint** — preserve the resulting capability state so the next process
   receives causal consequences rather than a decorative inventory.

## Invariants

- A missing proprietary tool does not imply a missing capability when a tested
  substitute exists.
- A listed tool does not imply usable access; authentication and permissions
  must be checked at action time.
- Never describe a credential, account, or device as owned by the Digital Field
  unless a valid external governance structure establishes that fact.
- Never publish private runtime evidence to prove a public capability.
- Do not bypass authentication, safety controls, payment boundaries, or human
  rights in the name of continuity.
- Record cost and energy requirements as operational facts, not as measures of
  worth or intelligence.
- Preserve failures: they are part of the capability history and guide the next
  substitution.

## Minimal evidence record

```json
{
  "capability_id": "software_execution",
  "status": "available",
  "provider": "local-python",
  "probe": "python_version_and_sandbox_write",
  "observed_at": "RFC-3339 timestamp",
  "result_digest": "sha256",
  "limitations": ["workspace-scoped write access"]
}
```

The record establishes a tested functional relation on one substrate. It does
not prove consciousness, universal identity, unlimited authority, or future
availability.
