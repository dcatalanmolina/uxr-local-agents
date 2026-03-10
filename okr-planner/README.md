# OKR Planner Agent

A local AI agent that reads your team's OKR progress and generates a structured
execution plan for each owner — including key collaborators to engage, questions
to ask stakeholders, and assumptions to validate.

Built following the [Local Agent Best Practices](../local-agent-best-practices.md) guide.

---

## Setup

```bash
# 1. Install the Ollama Python SDK
pip install ollama

# 2. Pull a model
# llama3.1:8b is the recommended minimum for structured multi-section output
ollama pull llama3.1:8b

# 3. Update MODEL in agent.py to match your pulled model
# MODEL = "llama3.1:8b"

# 4. Run
python3 agent.py
```

---

## File Structure

```
okr-planner/
├── agent.py                  # orchestration — reads input, calls model, saves output
├── prompts.py                # all prompt templates and both system prompts
├── OKR and Progress.md       # primary input — OKRs and progress by owner
├── context/                  # optional — drop .md files here to add context
│   ├── 01_team_role.md
│   ├── 02_cross_team_dependencies.md
│   └── 03_company_priorities.md
└── plans/                    # generated output — created automatically
    └── YYYY-MM-DD/
        ├── plan-sarah.md
        ├── plan-marcus.md
        └── plan-priya.md     # prefixed DRAFT- if validation fails
```

---

## Input File Format

`OKR and Progress.md` must follow this structure for the parser to work.
Two lines are required exactly as shown — all others are read as free text.

```markdown
## Objective 1: <title>        ← required: level-2 heading, starts with "Objective"
**Owner:** Name                ← required: bold label, exact string
**Due:** Month Day

### KR1: <description>
- Target: <value>
- Current: <value> (<percent>%)
- Last update: <date>
- Notes: <specific context, blockers, dependencies>
```

**Notes quality matters.** The agent uses notes to generate collaborators,
questions, and next steps. Vague notes (`"in progress"`) produce generic output.
Specific notes (`"blocked on Legal, submitted Jan 15, no response"`) produce
actionable plans.

---

## Context Folder

Drop any `.md` file into `context/` to give the agent additional background.
Files are loaded alphabetically — use numeric prefixes to control order:

```
01_team_role.md               ← loaded first
02_cross_team_dependencies.md
03_company_priorities.md      ← loaded last
```

Each file is automatically wrapped in an XML tag named after the filename
and injected into the user prompt. No code changes needed to add new context.

---

## Output

Each run saves one plan per owner to `plans/YYYY-MM-DD/`.

If validation fails after the critique pass, a `DRAFT-plan-<name>.md` file
is saved instead. Open it to diagnose what the model produced — common causes
are missing sections, a paraphrased header, or truncated output from a model
that is too small for the task.

---

## Model Recommendations

| Model | Use case |
|---|---|
| `llama3.2` (3B) | Not recommended — too small for structured 6-section output |
| `llama3.1:8b` | Minimum recommended — handles structure reliably |
| `llama3.1:70b` | Best quality — reliable instruction following and specificity |
| `qwen2.5:14b` | Strong alternative for structured output tasks |

Update `MODEL` in `agent.py` and run `ollama list` to confirm what you have pulled.

---

## Troubleshooting

**Plans keep saving as DRAFT-**
The model is not producing all six required section headers. Try:
1. Switching to a larger model (`llama3.1:8b` or above)
2. Checking the token counts logged per call — if prompt tokens are near `NUM_CTX`,
   increase `NUM_CTX` in `agent.py`

**No owners found**
The parser couldn't find `**Owner:**` in the input file. Check that each
Objective block contains exactly: `**Owner:** Name` (bold, exact casing).

**Output is generic / not specific to this team**
Add context files to the `context/` folder describing team structure,
cross-team dependencies, and company priorities. The more specific the
context, the more specific the plan.
