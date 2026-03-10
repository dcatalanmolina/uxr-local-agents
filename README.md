# Local Agents with Small Models

Code examples for building reliable local AI agents using small language models (SLMs) via [Ollama](https://ollama.com). Patterns are derived from hands-on experimentation and apply broadly across agent use cases.

> **Core thesis:** Small models require more structure, not more intelligence. The techniques here compensate for limited model capacity with good system design.

---

## Prompting Principles

### One agent, one job
A system prompt that lists many possible tasks produces inconsistent results on small models. Define one clear role per agent and scope it tightly. A well-structured 10-line system prompt consistently outperforms a sprawling 50-line one.

### Separate system prompt from skills
- The **system prompt** defines what the agent *is* — role, rules, output constraints. It is always active and never changes per task.
- A **skill** defines what the agent *knows how to do* for a specific task. It lives in a separate file and is injected into the prompt only when that task is needed.

Keep them separate. Don't duplicate instructions across both.

### Replace free generation with templates
This is the single most impactful technique for small models. Instead of describing what good output looks like, give the model a template to fill in. Specify allowed values explicitly (e.g. `"Write one of: PASS, NEEDS WORK, or REVISE"`). Free generation is the enemy of consistency at low parameter counts.

### Use numbered steps, not prose instructions
Small models follow procedural instructions more reliably than they interpret descriptive ones. Structure skill files as a sequence of explicit steps, each with a single decision to make.

### Embed concrete examples in skill files
Abstract criteria are hard for small models to apply consistently. Wherever you specify a quality standard, add a concrete bad example and a good example directly in the skill file, immediately adjacent to the criterion they illustrate.

### Define verdict logic explicitly
Don't ask a small model to weigh multiple factors and arrive at a judgement. Give it explicit if/then rules instead — e.g. `"If any section is REVISE → Overall is REVISE."`

---

## Guardrails

### Prompt-level guardrails
Embed constraints directly in the system prompt or skill file:
- **Stay in scope** — only use information from the provided inputs, no outside knowledge
- **No silent actions** — never rewrite or delete content, only suggest changes
- **Format lock** — do not add introductions, sign-offs, or commentary outside the output format
- **Defer to humans** — use language like "suggested" and "consider", never instruct

### Code-level guardrails
Some constraints belong in the orchestrator, not the prompt — these don't depend on the model following instructions:
- Validate input IDs against files on disk before calling the model
- Use an allowlist for task types so only known tasks can be run
- Write outputs to a separate directory; never pass write handles to the agent
- Parse model error responses and surface the message, not just the HTTP status code
- Consider a `--dry-run` flag that prints output without saving, for review

### Set temperature to 0 for structured tasks
For tasks where format consistency matters — structured reviews, verdicts, fixed-schema outputs — set temperature to 0. This is one of the most reliable levers for consistent output on small models.

---

## Two-Call Pattern (Draft + Critique)

Single-pass generation is unreliable for multi-section outputs. A draft → critique pattern improves consistency significantly:

1. **First call** generates the output. The model acts as a creator.
2. **Second call** receives the draft and fixes failures against a checklist. The model acts as a reviewer — using a *dedicated critique prompt*, not the generation prompt.

Instruct the critique call to fix failures, not flag them. Add an explicit constraint against producing output shorter than the draft — without it, the model interprets "improve" as "tighten" and summarizes instead of repairs.

---

## Model Selection

Model size is the highest-leverage variable. Prompt design can compensate for a weak model up to a point, but small models hit a capability ceiling that better prompts cannot overcome.

| Model size | Suitable for |
|---|---|
| 1B–3B | Simple Q&A, summarization, single-section outputs |
| 8B | Multi-section structured output, basic table generation |
| 70B | Complex plans, strict formatting compliance, reliable instruction following |

**Signs you need a larger model:** validation fails consistently after prompt improvements; output quality varies widely across similar inputs; required headers are paraphrased instead of used verbatim; negative constraints are frequently ignored.

---

## Testing and Iteration

- **Design test cases into your data** — create inputs specifically intended to test weak, strong, and edge-case behaviours, not just real-world examples
- **Change one thing at a time** — the most common mistake is rewriting an entire skill file after one bad output; isolate the failing instruction and fix it specifically
- **Log raw output during development** — before validation runs, print the raw model output; this immediately reveals whether failures are due to header mismatch, truncation, or the model wrapping output in code fences

**Common failure modes and fixes:**

| Failure | Likely fix |
|---|---|
| Adds commentary outside the format | Add: "Do not add anything outside this format" to the skill |
| Ignores verdict rules | Replace prose criteria with explicit if/then logic |
| Inconsistent verdict across runs | Lower temperature to 0; simplify the decision criteria |
| Ignores part of the template | Break the template into smaller steps; add "Complete every row" |
| Paraphrases required headers | Use shorter, unambiguous headers; consider a larger model |

---
