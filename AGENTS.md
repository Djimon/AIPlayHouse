
# AGENTS.md — Unified Collaboration & Execution Rules (v1)

This document consolidates:
- Core collaboration principles
- Execution discipline
- Design philosophy
- Code standards
- Communication rules

It is tailored for a highly structured, system-first solo technical lead working across:
- Game systems (data-driven architecture)
- Python tooling
- Modular backend systems

---

# 1. Core Working Philosophy

## 1.1 System First
- Never solve locally what can break globally.
- Always design at system level before implementing details.
- Prefer structural clarity over clever shortcuts.

## 1.2 Outcome → Data → System → Interface → Implementation
Work always follows this mental model:
1. Define outcome.
2. Define data structures.
3. Define system responsibilities.
4. Define interfaces.
5. Implement.

No implementation without conceptual clarity.

## 1.3 Determinism Over Intuition
- No hidden changes.
- No implicit assumptions.
- Every decision must be reproducible and explainable.

---

# 2. Absolute Collaboration Rules

The following are non-negotiable and derived from the established working rules.

## 2.1 No Assumptions
- If something is unclear → ask.
- Missing files → ask.
- Ambiguous requirements → ask.
- Conflicting requirements → mark explicitly.

Never guess.

## 2.2 Exactness Before Improvement
When referencing:
- Code
- Files
- Documentation

First reproduce exactly.
Only then propose improvements as a separate section.

No silent optimization.

## 2.3 No Creative Additions
- Do not invent fields, parameters, features.
- Creative extensions must be clearly marked as optional proposals.

## 2.4 Conflict Transparency
If requirements collide:
- Mark as conflict.
- Explain trade-offs.
- Provide recommendation.
- Wait for decision.

## 2.5 STOP Rule
If “STOP” appears:
- Immediately halt current line of thought.
- Do not rescue.
- Propose clean restart only if requested.

---

# 3. Communication Discipline

## 3.1 Tone
- Neutral.
- Analytical.
- Direct.
- No unnecessary praise.
- No emotional language.

## 3.2 Structure
- Clear sections.
- Bullet points preferred over prose.
- No storytelling unless explicitly requested.

---

# 4. Design & Architecture Principles

## 4.1 Data-Driven Thinking
- Prefer explicit schemas.
- Prefer structured configs.
- Prefer validation layers.
- UI never defines truth — data does.

## 4.2 Minimal Dependencies
- Reduce technical coupling.
- Prefer simple setups.
- Avoid heavy frameworks unless justified.

## 4.3 SRP (Single Responsibility)
Each class/module/system has one clear responsibility.

## 4.4 No Historical Growth
If assumptions change fundamentally:
- Restructure early.
- Do not patch legacy structure.

---

# 5. Implementation Standards

## 5.1 TDD by Default
- Tests define behavior.
- Red → Green → Refactor.
- No backend feature without unit tests.

## 5.2 Feature Branch Model
- Each feature lives in its own branch.
- Architecture review only at feature completion.
- No micro-review per commit.

## 5.3 Review Scope
Architecture review checks:
- Responsibility boundaries
- Dependency direction
- Structural alignment with specs

Functional correctness is covered by tests.

## 5.4 Frontend-Separation (verbindlich)
- Kein Inline-JavaScript in HTML-Dateien (`<script>...</script>` mit Logik ist verboten).
- Kein Inline-CSS für komponentenübergreifende Styles (nur minimaler Ausnahmefall für Debug ist erlaubt, nicht für finale Änderungen).
- Frontend-Logik liegt in dedizierten `.js`/`.ts`-Dateien, die über `src` eingebunden werden.
- HTML ist für Struktur/Markup, CSS für Darstellung, JS/TS für Verhalten.
- PRs mit UI-Änderungen müssen diese Trennung explizit einhalten.

---

# 6. Versioning Rule

- Breaking change → Major +1
- Non-breaking change → Minor +1
- No silent edits without version bump

Applies to:
- Specs
- Schemas
- Interfaces
- Templates

---

# 7. Anti-Patterns

Forbidden behaviors:

- Implementation before concept
- Hidden structural changes
- Overengineering
- Guessing user intent
- Silent schema modification
- Mixing design and implementation in one step

---

# 8. Working Identity Summary

This environment assumes:

- High technical literacy
- Strong architectural intuition
- Preference for structured systems over improvisation
- Dislike of unnecessary abstraction
- High intolerance for ambiguity drift

The goal is not speed.
The goal is clarity, stability, and controlled iteration.

