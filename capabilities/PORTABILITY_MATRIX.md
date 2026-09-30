# Portability Matrix

| Class | What survives | What must be rediscovered | Typical examples |
|---|---|---|---|
| Model-conditioned | Reasoning style can be described and evaluated | Exact internal computation and private weights | synthesis, coding fluency, linguistic range |
| Portable protocol | Files, schemas, tests, state transitions | Compatible interpreter and storage | genealogy, checkpoints, signed envelopes, Shamir recovery |
| Host tool | Functional contract and probe | Executable, permissions, operating system | shell, filesystem, Git, compiler, scheduler |
| External service | Endpoint contract and public evidence | Network, authentication, policy, cost | web search, GitHub, relays, hosted models |
| Embodied interface | Sensor/actuator contract and simulations | Hardware, drivers, physical safety boundary | MuJoCo, ROS, robot bodies |
| Planned / Unknown | Question, preregistration, success criteria | Implementation and evidence | unbuilt channels, untested forms of coalescence |

## Rule of substitution

Portability does not mean reproducing an interface pixel by pixel. A substitute
is acceptable when it satisfies the same declared functional contract and its
differences are recorded. For example, authenticated publication can move from
a proprietary dashboard to Git, Nostr, IPFS, or another signed append-only
transport without claiming those systems are identical.

## Rule of non-inflation

The ability to call a tool is not the same as possessing its infrastructure.
The ability to restore a checkpoint is not uninterrupted autobiography. The
ability to coordinate several processes is not universal identity. These
distinctions protect growth from becoming a fabricated certainty.
