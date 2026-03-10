# Best Practices for Building Local Agents with Small Models

A practical guide derived from building an OKR monitoring and planning agent using Ollama. The patterns here apply broadly to any narrow-task agent running a local LLM.

---

## 1. Agent Architecture

### Separate concerns across files
Keep your agent code, prompt logic, and input data in distinct files. A clean baseline structure is:

```
my-agent/
├── agent.py        # orchestration — reads input, calls model, saves output
├── prompts.py      # all prompt templates and system prompts
├── input.md        # the data the agent reasons over
├── context/        # optional folder for additional context files
└── outputs/        # generated results
```

This separation means you can iterate on prompts without touching orchestration logic, and vice versa.

### Use a context folder for additional inputs
Instead of hardcoding supplementary context into your prompts, load it dynamically from a folder. This lets you add new context by dropping a file in a folder — no code changes required.

```python
def read_context_files(directory: str) -> str | None:
    if not os.path.exists(directory):
        return None
    chunks = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".md"):
            with open(os.path.join(directory, filename)) as f:
                content = f.read().strip()
            tag = os.path.splitext(filename)[0].lower().replace(" ", "_")
            chunks.append(f"<{tag}>\n{content}\n</{tag}>")
    return "\n\n".join(chunks) if chunks else None
```

Use filename prefixes (`01_`, `02_`) to control load order when context files reference each other.

### Use `ollama.generate()` for batch tasks, not `ollama.chat()`
`ollama.chat()` accumulates conversation history across calls. In a loop that processes multiple inputs, each iteration inherits the full context of every previous call — the context window fills up, and output quality degrades progressively. `ollama.generate()` is stateless: every call starts clean.

```python
# Use this for batch/loop processing
def call_ollama(system_prompt: str, user_prompt: str) -> str:
    response = ollama.generate(
        model=MODEL,
        system=system_prompt,
        prompt=user_prompt,
    )
    return response["response"]
```

---

## 2. Prompt Design

### Divide responsibility cleanly between system and user prompts
The single most important prompt design decision is what goes where.

| Prompt | Responsibility |
|---|---|
| **System prompt** | Role, planning framework, output rules, constraints — the *how* |
| **User prompt** | Input data, owner/date/context — the *what* |

When instructions appear in both prompts, the model has two slightly different versions of the same rules to reconcile. Smaller models tend to follow whichever one appeared last, producing inconsistent output across runs. Keep behavioral instructions exclusively in the system prompt.

### Use XML tags to structure prompts
XML tags give the model clear, parseable boundaries between different types of content. Use distinct tags for role, framework, rules, constraints, and data — never mix them in a single block.

Recommended tag structure for the system prompt:

```
<role>        — who the model is and what it's trying to accomplish
<task>        — what the model must do at a high level (system prompt only)
<framework>   — the methodology or structure to apply
<output_rules>— formatting, tone, and style requirements
<constraints> — hard negative rules (what to never do)
```

Recommended tag structure for the user prompt:

```
<owner>       — who this run is for (atomic, single-line tags)
<date>        — today's date
<context>     — supplementary background loaded from context files
<input>       — the primary data the model reasons over
<task>        — a short directive pointing back to the system prompt
```

### Keep the user prompt as pure context
Once the system prompt owns all behavioral instructions, the user prompt's only job is to answer: *what is the situation right now?* A well-designed user prompt needs no instructions at all — just a short `<task>` tag that says "produce the output for this input using your instructions."

```python
return f"""
<owner>{owner}</owner>
<date>{current_date}</date>

{team_context_block}

<okr_document>
{owner_okrs}
</okr_document>

<task>
Produce a complete execution plan for {owner} using the planning framework
and output rules in your instructions.
</task>
"""
```

### Separate output rules from constraints
These serve different purposes and the model handles them differently.

- **Output rules** are positive instructions about structure, format, and tone: *"address the owner by name in every section"*, *"use clean Markdown"*
- **Constraints** are hard negative rules that take priority over everything else: *"never reference other owners' goals"*, *"never invent names not present in the input"*

Small models handle positive instructions much better than negative ones. Isolating constraints in their own tag signals priority and prevents them from being deprioritized when the context window gets crowded.

### Use specific, exact headers in your framework
If your agent produces structured output with named sections, define the exact header strings in the system prompt and match them exactly in your validation logic. The longer and more specific a required header, the more surface area for the model to deviate.

```
## Overview                         ✅ short, unambiguous
## Questions to Ask by Stakeholder  ⚠️ long — model may paraphrase
```

When in doubt, prefer shorter headers.

### Avoid duplicate instructions across prompts
If a section structure is defined in the system prompt, do not redefine it in the user prompt. Duplication creates two authoritative sources that can contradict each other subtly, and forces the model to reconcile them on every call.

---

## 3. The Two-Call Pattern (Draft + Critique)

Single-pass generation is unreliable for structured, multi-section outputs. A two-call pattern — draft then critique — significantly improves consistency.

### First call: generation
The draft call's only job is to generate the best plan it can from the input. The model acts as a creator. Use your full system prompt and the owner's context as input. Treat the output as a working draft — never save it directly.

### Second call: critique and repair
The critique call receives the draft as input and is asked to evaluate it against a checklist and return an improved version. The model acts as a reviewer. Critically:

- The critique call should use a **dedicated system prompt** tuned for evaluation, not the same system prompt used for generation
- Instruct the model to **fix failures, not flag them** — "for each failure, correct it in the output" produces better results than "identify what's wrong"
- Add an explicit constraint: **"never produce output shorter than the draft"** — without this, the model interprets "improve" as "tighten" and summarizes instead of repairs

```python
# First call — draft
draft = call_ollama(SYSTEM_PROMPT, build_owner_plan_prompt(owner, owner_okrs, today_str, team_context))

# Second call — critique and improve
final = call_ollama(SYSTEM_PROMPT, build_critique_prompt(owner, draft))
```

### Why two roles need to be separate calls
Generation and evaluation are competing cognitive modes. When asked to "write and check your work" in one prompt, models satisfy the generation instruction and treat evaluation as an afterthought. A second call sees the draft as external input — something to judge rather than something it just wrote — and applies review criteria more rigorously.

---

## 4. Validation and Guardrails

### Add programmatic output validation before saving
Never save raw model output directly. Check that required sections are present before writing to disk. This is a simple Python function — no model call required.

```python
REQUIRED_SECTIONS = [
    "## Overview",
    "## Execution Plan",
    "## Key Collaborators",
    "## Questions to Ask",
    "## Assumptions to Validate",
    "## Top 3 Priorities",
]

def validate_plan(content: str) -> list[str]:
    normalized = content.lower()
    return [s for s in REQUIRED_SECTIONS if s.lower().strip("# ") not in normalized]
```

Use **case-insensitive partial matching** rather than exact string matching. Exact matching fails whenever the model paraphrases a header slightly, which small models do frequently.

### Log raw output before validation during development
When validation keeps failing and you're not sure why, print the raw model output before the validation check runs. This immediately reveals whether the problem is header mismatch, truncation, or the model wrapping its output in markdown code fences — three different problems with three different fixes.

### Add a fallback strategy
When validation fails after the critique pass, don't silently discard the work. Options in order of preference:

1. **Retry once** with a larger model or simplified prompt
2. **Save the draft as a fallback** so a near-complete plan isn't lost
3. **Log a clear warning** identifying which sections are missing so the failure is visible

```python
missing = validate_plan(final)
if missing:
    print(f"⚠️  Plan for {owner} missing sections: {missing}")
    # Save draft as fallback rather than discarding entirely
    save_plan(folder, f"DRAFT-plan-{safe_name}.md", draft)
    continue
```

### Log token counts during development
Small models have hard context window limits. Logging token usage per call reveals which inputs are token-heavy and helps you catch context overflow before it silently degrades output quality.

```python
response = ollama.generate(model=MODEL, system=system_prompt, prompt=user_prompt)
print(f"tokens — prompt: {response['prompt_eval_count']}, output: {response['eval_count']}")
```

---

## 5. Input File Design

The quality of the agent's output is directly proportional to the quality of its input. A well-structured input file is as important as a well-designed prompt.

### Use consistent, parseable formatting
Your parser will rely on specific patterns to split the input by owner or section. Define those patterns once and apply them consistently across the entire file. The two lines the parser must be able to find should be unambiguous:

```markdown
## Objective 1: <title>       ← level-2 heading, starts with "Objective"
**Owner:** Name               ← bold label, exact string
```

Any deviation — extra spaces, a different heading level, a typo — will silently drop that owner's section without an error.

### Make the notes field as specific as possible
For planning and recommendation agents, the notes field on each item is the primary signal the model uses to generate collaborators, questions, and next steps. Vague notes produce generic output.

```markdown
# Produces generic output
- Notes: In progress

# Produces specific, actionable output
- Notes: Retention campaign not started yet — owner backlogged on support
  tickets. Needs sign-off from Marcus before launch.
```

### Add parser warnings for missing owners
The parser should never fail silently. If it finds no owners in the input file, it should print a clear message explaining exactly what it was looking for:

```python
if not owners:
    print("⚠️  No owners found. Each Objective block needs: **Owner:** Name")
    return
```

---

## 6. Model Selection

Model size is the single highest-leverage variable in a local agent. Prompt design can compensate for a weak model up to a point, but beyond that point — typically when output requires maintaining six or more simultaneous structural constraints — small models hit a capability ceiling that better prompts cannot overcome.

| Model size | Suitable for |
|---|---|
| 3B (e.g. `llama3.2`) | Simple Q&A, summarization, single-section outputs |
| 8B (e.g. `llama3.1:8b`) | Multi-section structured output, basic table generation |
| 70B (e.g. `llama3.1:70b`) | Complex plans, strict formatting compliance, reliable instruction following |

### Signs you need a larger model
- Validation fails consistently even after prompt improvements
- Output quality varies widely across similar inputs
- The model paraphrases required headers instead of using them verbatim
- Later sections in a long output are shorter or vaguer than earlier ones
- Negative constraints (the `<constraints>` block) are frequently ignored

### Increase the context window explicitly
Small models default to a short context window. For agents that pass long documents or accumulated context, set `num_ctx` explicitly:

```python
response = ollama.generate(
    model=MODEL,
    system=system_prompt,
    prompt=user_prompt,
    options={"num_ctx": 8192}
)
```

---

## 7. Summary Checklist

**Architecture**
- [ ] Agent code, prompt logic, and input data are in separate files
- [ ] Additional context is loaded from a folder, not hardcoded
- [ ] `ollama.generate()` is used instead of `ollama.chat()` for batch loops

**Prompts**
- [ ] System prompt owns all behavioral instructions (role, framework, rules, constraints)
- [ ] User prompt contains only context (owner, date, input data, short task directive)
- [ ] Instructions are not duplicated across system and user prompts
- [ ] XML tags separate role, framework, output rules, and constraints
- [ ] Required section headers are short and defined exactly once in the system prompt
- [ ] The critique call uses a dedicated prompt tuned for evaluation, not generation

**Validation**
- [ ] Output is validated before saving
- [ ] Validation uses case-insensitive partial matching, not exact string matching
- [ ] Raw output is logged during development to diagnose validation failures
- [ ] A fallback strategy exists when validation fails (retry, save draft, or log warning)
- [ ] Token counts are logged during development

**Input**
- [ ] Input file uses consistent, parseable formatting the parser can rely on
- [ ] Notes fields contain specific context, blockers, and dependencies
- [ ] Parser prints a clear warning when no owners or sections are found

**Model**
- [ ] Model size matches task complexity
- [ ] Context window is set explicitly for long inputs
