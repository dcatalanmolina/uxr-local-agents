import ollama
import os
import re
from datetime import date
from prompts import DRAFT_SYSTEM_PROMPT, CRITIQUE_SYSTEM_PROMPT
from prompts import build_draft_prompt, build_critique_prompt

# ── Configuration ──────────────────────────────────────────────────────────────

OKR_FILE    = "OKR and Progress.md"
CONTEXT_DIR = "context"
PLANS_DIR   = "plans"
MODEL       = "gemma3:1b"   # swap for any model you have pulled locally
NUM_CTX     = 8192         # context window size — increase for long input files

# Short headers are more reliably matched than long ones.
# These must match the headers defined in DRAFT_SYSTEM_PROMPT exactly.
REQUIRED_SECTIONS = [
    "## Overview",
    "## Execution Plan",
    "## Collaborators",
    "## Questions",
    "## Assumptions",
    "## Top 3 Priorities",
]


# ── Input readers ──────────────────────────────────────────────────────────────

def read_okr_file(path: str) -> str:
    """Reads the primary OKR input file. Hard-fails if missing."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Could not find '{path}'.\n"
            f"Make sure '{OKR_FILE}' is in the same folder as agent.py.\n"
            f"Expected format: each Objective block must include **Owner:** Name"
        )
    with open(path, "r") as f:
        return f.read()


def read_context_files(directory: str) -> str | None:
    """
    Loads all .md files from the context folder alphabetically.
    Each file is wrapped in an XML tag named after the filename.
    Returns None if the folder doesn't exist — agent proceeds without context.
    Use filename prefixes (01_, 02_) to control load order.
    """
    if not os.path.exists(directory):
        return None

    chunks = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".md"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r") as f:
                content = f.read().strip()
            tag = os.path.splitext(filename)[0].lower().replace(" ", "_")
            chunks.append(f"<{tag}>\n{content}\n</{tag}>")

    return "\n\n".join(chunks) if chunks else None


# ── Parser ─────────────────────────────────────────────────────────────────────

def parse_objectives_by_owner(okr_content: str) -> dict:
    """
    Splits the OKR file into per-owner sections.
    Looks for '## Objective' headings and extracts the **Owner:** field from each.
    Returns { owner_name: markdown_block }.

    Input file requirements:
    - Objectives must use level-2 headings starting with 'Objective'
    - Each block must contain a line formatted as: **Owner:** Name
    """
    sections = re.split(r'(?=^## Objective)', okr_content, flags=re.MULTILINE)

    owners = {}
    for section in sections:
        if not section.strip():
            continue
        match = re.search(r'\*\*Owner:\*\*\s*(.+)', section)
        if match:
            owner = match.group(1).strip()
            # An owner may have multiple objectives — append if already seen
            if owner in owners:
                owners[owner] += "\n\n" + section.strip()
            else:
                owners[owner] = section.strip()

    return owners


# ── Model call ─────────────────────────────────────────────────────────────────

def call_ollama(system_prompt: str, user_prompt: str, label: str = "") -> str:
    """
    Stateless call using ollama.generate() — safe for use in loops.
    Use ollama.generate(), not ollama.chat(). chat() accumulates history
    across calls, filling the context window and degrading output quality
    for every owner after the first.
    """
    response = ollama.generate(
        model=MODEL,
        system=system_prompt,
        prompt=user_prompt,
        options={"num_ctx": NUM_CTX}
    )

    # Token logging — helps diagnose context overflow during development
    prompt_tokens  = response.get("prompt_eval_count", "?")
    output_tokens  = response.get("eval_count", "?")
    tag = f" [{label}]" if label else ""
    print(f"   📊 tokens{tag} — prompt: {prompt_tokens}, output: {output_tokens}")

    return response["response"]


# ── Validation ─────────────────────────────────────────────────────────────────

def validate_plan(content: str) -> list[str]:
    """
    Case-insensitive partial matching against REQUIRED_SECTIONS.
    Partial matching is more resilient than exact matching — small models
    frequently paraphrase headers slightly, which exact matching would fail.
    Returns a list of missing sections, empty list if all present.
    """
    normalized = content.lower()
    return [
        s for s in REQUIRED_SECTIONS
        if s.lower().lstrip("# ") not in normalized
    ]


# ── Output ─────────────────────────────────────────────────────────────────────

def save_plan(folder: str, filename: str, content: str) -> str:
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    with open(path, "w") as f:
        f.write(content)
    return path


# ── Main ───────────────────────────────────────────────────────────────────────

def run_planning_agent():
    today     = date.today()
    today_str = today.strftime("%B %d, %Y")
    date_slug = str(today)

    # ── Read inputs ───────────────────────────────────────────────────────────
    print("📋 Reading OKR file...")
    okr_content = read_okr_file(OKR_FILE)

    print("📂 Loading context files...")
    team_context = read_context_files(CONTEXT_DIR)
    if team_context:
        loaded = [f for f in sorted(os.listdir(CONTEXT_DIR)) if f.endswith(".md")]
        print(f"   ✅ Loaded {len(loaded)} context file(s): {', '.join(loaded)}")
    else:
        print(f"   ℹ️  No context folder found — proceeding without it.")

    # ── Parse owners ──────────────────────────────────────────────────────────
    owners = parse_objectives_by_owner(okr_content)

    if not owners:
        print("\n⚠️  No owners found in the OKR file. Cannot generate plans.")
        print("   Each Objective block must include a line like: **Owner:** Name")
        return

    print(f"\n👥 Found {len(owners)} owner(s): {', '.join(owners.keys())}")

    # ── Process each owner ────────────────────────────────────────────────────
    for owner, owner_okrs in owners.items():
        print(f"\n🗺️  Generating plan for {owner}...")
        safe_name   = owner.lower().replace(" ", "-")
        output_folder = f"{PLANS_DIR}/{date_slug}"

        # First call — draft (generation)
        print(f"   ✍️  Draft pass...")
        draft = call_ollama(
            system_prompt=DRAFT_SYSTEM_PROMPT,
            user_prompt=build_draft_prompt(owner, owner_okrs, today_str, team_context),
            label="draft"
        )

        # Second call — critique and repair (evaluation)
        # Uses a dedicated CRITIQUE_SYSTEM_PROMPT — not the same system prompt
        # as the draft call. Generation and evaluation are different tasks.
        print(f"   🔍 Critique pass...")
        final = call_ollama(
            system_prompt=CRITIQUE_SYSTEM_PROMPT,
            user_prompt=build_critique_prompt(owner, draft),
            label="critique"
        )

        # Validate before saving
        missing = validate_plan(final)

        if missing:
            print(f"\n⚠️  Final plan for {owner} is missing sections: {missing}")
            print(f"   Saving draft as fallback — review manually.")
            save_plan(
                folder=output_folder,
                filename=f"DRAFT-plan-{safe_name}.md",
                content=f"# DRAFT — Execution Plan — {owner} — {today_str}\n\n{draft}"
            )
            continue

        # Save final plan
        plan_path = save_plan(
            folder=output_folder,
            filename=f"plan-{safe_name}.md",
            content=f"# Execution Plan — {owner} — {today_str}\n\n{final}"
        )
        print(f"   ✅ Saved to {plan_path}")

    print(f"\n🎉 Done. Plans saved to {PLANS_DIR}/{date_slug}/")


if __name__ == "__main__":
    run_planning_agent()
