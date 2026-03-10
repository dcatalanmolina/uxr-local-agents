"""
orchestrator.py
Core logic for the UX Insights Agent.
Loads skills, assembles prompts, and calls the Ollama API.
"""

import os
import json
import urllib.request
import urllib.error
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent.parent
SKILLS_DIR  = BASE_DIR / "skills"
INSIGHTS_DIR = BASE_DIR / "insights"
OUTPUTS_DIR = BASE_DIR / "outputs"
SYSTEM_PROMPT_PATH = Path(__file__).parent / "system_prompt.txt"

# ── Skill registry ─────────────────────────────────────────────────────────────
SKILL_MAP = {
    "clarity":   "skill_clarity_review.md",
    "redundancy": "skill_redundancy_check.md",
    "executive": "skill_executive_summary.md",
}

# ── Ollama config ──────────────────────────────────────────────────────────────
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:1b")


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def load_skill(task_type: str) -> str:
    filename = SKILL_MAP.get(task_type)
    if not filename:
        raise ValueError(
            f"Unknown task type '{task_type}'. "
            f"Valid options: {list(SKILL_MAP.keys())}"
        )
    skill_path = SKILLS_DIR / filename
    if not skill_path.exists():
        raise FileNotFoundError(f"Skill file not found: {skill_path}")
    return skill_path.read_text(encoding="utf-8").strip()


def load_insights(insight_ids: list[str]) -> str:
    """
    Load one or more insight files by ID (e.g. ['INS-001', 'INS-002']).
    Matches by prefix so the full filename doesn't need to be known.
    """
    loaded = []
    for insight_id in insight_ids:
        matches = list(INSIGHTS_DIR.glob(f"{insight_id}*.md"))
        if not matches:
            raise FileNotFoundError(
                f"No insight file found for ID '{insight_id}' in {INSIGHTS_DIR}"
            )
        loaded.append(matches[0].read_text(encoding="utf-8").strip())
    separator = "\n\n" + "─" * 60 + "\n\n"
    return separator.join(loaded)


def build_prompt(task_type: str, insight_ids: list[str]) -> tuple[str, str]:
    """Returns (system_prompt, user_message)."""
    base_system  = load_system_prompt()
    skill        = load_skill(task_type)
    insight_text = load_insights(insight_ids)

    system = f"{base_system}\n\n---\n\n{skill}"
    user   = f"Here are the insights to work with:\n\n{insight_text}"
    return system, user


def call_ollama(system: str, user_message: str) -> str:
    payload = json.dumps({
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_message},
        ],
        "stream": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(body).get("error", body)
        except json.JSONDecodeError:
            detail = body or "(no details returned)"
        raise RuntimeError(f"Ollama API error {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise ConnectionError(
            f"Could not connect to Ollama at {OLLAMA_URL}.\n"
            "Make sure Ollama is running: `ollama serve`"
        )


def save_output(task_type: str, insight_ids: str, result: str) -> Path:
    OUTPUTS_DIR.mkdir(exist_ok=True)
    ids_slug = "_".join(insight_ids).replace("-", "").lower()
    filename = f"{task_type}_{ids_slug}.md"
    output_path = OUTPUTS_DIR / filename
    output_path.write_text(result, encoding="utf-8")
    return output_path


def run(task_type: str, insight_ids: list[str], save: bool = True) -> str:
    """
    Main entry point.
    task_type:   'clarity' | 'redundancy' | 'executive'
    insight_ids: list of IDs e.g. ['INS-001'] or ['INS-001', 'INS-002']
    """
    print(f"\n▶ Task:     {task_type}")
    print(f"▶ Insights: {', '.join(insight_ids)}")
    print(f"▶ Model:    {OLLAMA_MODEL}\n")

    system, user = build_prompt(task_type, insight_ids)
    print("Calling Ollama... (this may take a moment)\n")
    result = call_ollama(system, user)

    if save:
        output_path = save_output(task_type, insight_ids, result)
        print(f"✓ Output saved to: {output_path}\n")

    return result
