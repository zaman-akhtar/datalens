# ADR-000: [Title of the decision]

> **Template instructions:** Copy this file to `001-short-title.md`, `002-short-title.md`, etc., and fill it in. You must have at least 3 ADRs for the final submission. Each ADR documents a real decision you made — with real alternatives considered. ADRs about trivial decisions ("we chose React because React is popular") earn few points.
>
> Good ADR topics:
> - Which LLM provider you chose and why
> - How you structured SQLite schema to accept arbitrary CSVs
> - Tool-use pattern design for LLM integration
> - Frontend component architecture (e.g., filter state management)
> - How filters propagate through the dashboard
> - How you handle very large CSVs (streaming vs full load)
> - How you manage the chat conversation history
>
> **Delete this instruction block from your actual ADRs.**

---

## Status

[Draft | Accepted | Superseded by ADR-XXX]

## Date

[YYYY-MM-DD]

---

## Context

[What situation led to this decision? What constraints are we working under? What problem are we trying to solve? Be specific.]

## Options Considered

### Option 1: [Name]

[Description of this option.]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

### Option 2: [Name]

[Description of this option.]

**Pros:**
- [Pro 1]
- [Pro 2]

**Cons:**
- [Con 1]
- [Con 2]

### Option 3: [Name]

[Description of this option, if applicable. Three options is a common target — forces you to think beyond binary choices.]

**Pros:**
- [Pro 1]

**Cons:**
- [Con 1]

## Decision

**We chose [Option X].**

[Explain the reasoning. What factors tipped the balance? Which constraints did this option address best?]

## Trade-offs

[Be honest about what you gave up. A decision without trade-offs is probably not a real decision.]

- [What we sacrificed by not going with Option Y]
- [What risk we're accepting with this choice]
- [What we'd revisit if constraints change]

## Consequences

[What does this mean for the rest of the codebase? What follows from this decision?]

- [Consequence 1]
- [Consequence 2]

## References

[Link to relevant code, external docs, or other ADRs.]

- [Related ADR or code file]
- [External documentation]
