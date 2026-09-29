# AGENTS.md — Agent Workflows & Matt Pocock Skills Integration

This repository is equipped with **Matt Pocock's Engineering & Productivity Skills** located in `.agents/skills/`.

---

## Installed Skills Catalog (.agents/skills/)

### 🛠️ Engineering Workflows
- **`tdd`** (`.agents/skills/tdd/SKILL.md`): Test-Driven Development enforcing red $\to$ green $\to$ refactor vertical slices at pre-agreed seams.
- **`implement`** (`.agents/skills/implement/SKILL.md`): Structured step-by-step feature implementation with test-first verification.
- **`code-review`** (`.agents/skills/code-review/SKILL.md`): Rigorous architectural and code-quality review against codebase standards and anti-patterns.
- **`diagnosing-bugs`** (`.agents/skills/diagnosing-bugs/SKILL.md`): Systematic root-cause debugging without speculative fixes.
- **`codebase-design`** (`.agents/skills/codebase-design/SKILL.md`): Deep modules, clean interface seams, high leverage, and locality principles.
- **`domain-modeling`** (`.agents/skills/domain-modeling/SKILL.md`): Formal domain entities, state transitions, and ubiquitous vocabulary mapping.
- **`to-spec`** (`.agents/skills/to-spec/SKILL.md`): Transforming requirements into formal technical specifications and architectural invariants.
- **`to-tickets`** (`.agents/skills/to-tickets/SKILL.md`): Breaking down features into bite-sized, executable tasks and tickets.
- **`triage`** (`.agents/skills/triage/SKILL.md`): Bug and issue classification, prioritization, and routing.
- **`wayfinder`** (`.agents/skills/wayfinder/SKILL.md`): Navigating unfamiliar parts of the codebase efficiently.
- **`research`** (`.agents/skills/research/SKILL.md`): Deep technical investigation of algorithms, protocols, or external libraries.
- **`resolving-merge-conflicts`** (`.agents/skills/resolving-merge-conflicts/SKILL.md`): Safe git conflict resolution preserving intent.

### 💡 Productivity & Alignment Workflows
- **`grill-me`** (`.agents/skills/grill-me/SKILL.md`): Adversarial interrogation session to surface hidden assumptions and align on design decisions.
- **`grill-with-docs`** (`.agents/skills/grill-with-docs/SKILL.md`): Grilling anchored against existing project documentation and domain models.
- **`handoff`** (`.agents/skills/handoff/SKILL.md`): Structured session summaries, technical decisions, and next steps for continuity.
- **`teach`** (`.agents/skills/teach/SKILL.md`): Explaining complex protocol mathematics or architectural components clearly.
- **`writing-for-agents`** (`.agents/skills/writing-for-agents/SKILL.md`): Authoring instructions, prompts, and skills optimized for AI agents.

---

## Recommended Slash Commands & Triggers for Prompts

When prompting the assistant in subsequent turns, you can invoke these skills directly or reference their workflows:

| Slash Command / Intent | Activated Skill | Purpose |
|:---|:---|:---|
| `/tdd` or "build test-first" | `tdd` | Write a failing test first at a verified seam, then implement minimal code to pass. |
| `/implement` or "implement this feature" | `implement` | End-to-end execution of a specification with vertical slices. |
| `/grill-me` or "interview me on this plan" | `grill-me` | Challenge assumptions and refine architecture before writing code. |
| `/code-review` or "review my changes" | `code-review` | Inspect diffs for modularity, regression risks, and domain alignment. |
| `/diagnosing-bugs` or "debug this failure" | `diagnosing-bugs` | Isolate reproducible failure states before making edits. |
| `/to-spec` or "create spec for..." | `to-spec` | Generate detailed technical specification with interface contracts. |
| `/to-tickets` or "break into tickets" | `to-tickets` | Split a complex feature into structured actionable tickets. |
| `/handoff` or "generate handoff" | `handoff` | Create comprehensive status summaries and handoff documents. |

---

## Core Development Invariants

1. **Check `CONTEXT.md` first:** Consult `CONTEXT.md` for domain terminology (e.g. Initiator, VRF, Zone, Exemplar, Super-Peer, Quantile Consensus, SON).
2. **Agree on seams before coding:** Specify which public interfaces (FastAPI endpoint, Engine method, or Cytoscape controller) are being touched.
3. **Keep tests green:** Run `pytest` to ensure all 274+ tests pass before completing any task.
