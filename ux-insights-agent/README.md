# UX Insights Agent

A local AI agent that helps junior UX researchers maintain and communicate research insights. Powered by Ollama.

---

## Setup

### 1. Install Ollama
Download from [ollama.com](https://ollama.com) and install for your OS.

### 2. Pull a model
```bash
ollama pull llama3
```
> For better quality on long documents, try `ollama pull mistral` or `ollama pull llama3:8b-instruct-q5_K_M`

### 3. Start Ollama
```bash
ollama serve
```

### 4. Install Python dependencies
```bash
pip install requests
```

### 5. Run the agent
```bash
python run.py --task clarity --insights INS-004
```

---

## Project Structure

```
ux-insights-agent/
│
├── run.py                        # CLI entry point
│
├── agent/
│   ├── orchestrator.py           # Core logic: loads skills, calls Ollama
│   └── system_prompt.txt         # The agent's base identity and rules
│
├── skills/
│   ├── skill_clarity_review.md   # How to review an insight for clarity
│   ├── skill_redundancy_check.md # How to detect overlapping insights
│   └── skill_executive_summary.md # How to write C-suite summaries
│
├── insights/                     # Your markdown insight files
│   ├── INS-001_checkout-dropoff.md
│   ├── INS-002_onboarding-confusion.md
│   ├── INS-003_search-abandonment.md
│   └── INS-004_dashboard-confusion.md   ← intentionally weak, good for clarity testing
│
└── outputs/                      # Agent results are saved here
```

---

## Usage

### Review an insight for clarity
Best used on a single insight. INS-004 is intentionally weak — good first test.
```bash
python run.py --task clarity --insights INS-004
```

### Check multiple insights for redundancy
INS-001 and INS-003 share session data and overlap thematically.
```bash
python run.py --task redundancy --insights INS-001 INS-002 INS-003
```

### Draft an executive summary
```bash
python run.py --task executive --insights INS-001
```

Combine multiple insights into one summary:
```bash
python run.py --task executive --insights INS-001 INS-003
```

### Options
| Flag | Description |
|---|---|
| `--task` | `clarity`, `redundancy`, or `executive` |
| `--insights` | One or more insight IDs (e.g. `INS-001 INS-002`) |
| `--model` | Override model (e.g. `--model mistral`) |
| `--no-save` | Print only, don't write to `outputs/` |

---

## Adding New Insights

Create a new markdown file in `insights/` using this format:

```
# INS-XXX: [Insight Title]

## Statement
[One clear, specific, falsifiable claim.]

## Evidence

### [Source Name + Date]
[Data, observations, or quotes that support the statement.]

## Argument
[Logical reasoning that connects the evidence to the statement.]
```

Name the file `INS-XXX_short-slug.md` and the agent will find it automatically.

---

## Adding New Skills

1. Create a new `.md` file in `skills/`
2. Register it in `agent/orchestrator.py` in the `SKILL_MAP` dictionary:

```python
SKILL_MAP = {
    "clarity":    "skill_clarity_review.md",
    "redundancy": "skill_redundancy_check.md",
    "executive":  "skill_executive_summary.md",
    "your_skill": "skill_your_skill.md",   # ← add here
}
```

3. Use it: `python run.py --task your_skill --insights INS-001`

---

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api/chat` | Ollama API endpoint |
| `OLLAMA_MODEL` | `llama3` | Model to use |

Override inline:
```bash
OLLAMA_MODEL=mistral python run.py --task clarity --insights INS-004
```
