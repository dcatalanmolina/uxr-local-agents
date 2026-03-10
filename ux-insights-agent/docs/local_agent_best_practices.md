Best Practices for Building

**Local AI Agents**

*Consistent outputs, effective prompting, and guardrail design*

Derived from practical experimentation with Ollama and small language models

**1. Introduction**

This document captures practical lessons learned from designing and building local AI agents powered by small language models (SLMs) running via Ollama. It is intended for engineers and researchers who want to deploy narrow-purpose agents that produce reliable, consistent results without depending on large cloud-hosted models.

The core thesis is simple: small models require more structure, not more intelligence. The techniques here are about compensating for limited model capacity with good system design --- clear prompts, modular skills, explicit output formats, and well-scoped agent responsibilities.

+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Who this is for**                                                                                                                                                           |
|                                                                                                                                                                               |
| Engineers building local automation pipelines, researchers exploring agentic workflows, and teams evaluating whether small models can replace larger ones for specific tasks. |
+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**2. Core Concepts**

Before diving into best practices, it helps to be precise about the building blocks. Two concepts are central to this framework.

**2.1 System Prompts**

A system prompt is a set of instructions loaded at the start of every conversation. Think of it as the agent\'s job description --- it defines who the agent is, what it is allowed to do, and how it should behave in all situations. It is always active.

  ------------------------ --------------------------------------------------------
  **Aspect**               **Description**

  When loaded              Every single turn, before any user message

  What it contains         Role definition, behavioural rules, output constraints

  Analogy                  An employee handbook --- always applies

  Scope                    Global --- governs all tasks the agent performs
  ------------------------ --------------------------------------------------------

**2.2 Skills**

A skill is task-specific knowledge stored in a separate file and injected into the prompt only when that task is needed. Rather than loading all knowledge upfront, skills are loaded on demand by the orchestrator. This keeps the base agent lean and makes the system easy to extend.

  ------------------------ ----------------------------------------------------
  **Aspect**               **Description**

  When loaded              Only when the task requires it

  What it contains         Step-by-step instructions for a specific task type

  Analogy                  A workshop manual --- consulted per job

  Scope                    Local --- applies only to the current task
  ------------------------ ----------------------------------------------------

+--------------------------------------------------------------------------------------------------------------------------------------+
| **The golden rule**                                                                                                                  |
|                                                                                                                                      |
| The system prompt defines what the agent is. A skill defines what the agent knows how to do for a specific task. Keep them separate. |
+--------------------------------------------------------------------------------------------------------------------------------------+

**3. Agent Architecture**

A well-structured local agent system has three layers. Keeping these layers separate makes the system easier to debug, extend, and maintain.

**3.1 The Three Layers**

  ------------------------ -----------------------------------------------------------------------------------------
  **Layer**                **Responsibility**

  Agent identity           The system prompt. Defines role, rules, and output constraints. Never changes per task.

  Skills                   Markdown files loaded per task. Contain step-by-step instructions and output templates.

  Repository / data        The files the agent reads and writes to. Kept separate from agent logic.
  ------------------------ -----------------------------------------------------------------------------------------

**3.2 The Orchestrator**

The orchestrator is the glue. It detects the task type, loads the appropriate skill file, assembles the final prompt, calls the model, and optionally saves the output. It should be thin --- its job is routing, not reasoning.

-   Detect intent from user input or a UI control

-   Load the matching skill file from disk

-   Concatenate: system prompt + skill + insight/data content

-   Call the model with the assembled prompt

-   Save output to a designated outputs directory

+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Design principle**                                                                                                                                                                                        |
|                                                                                                                                                                                                             |
| The agent proposes, humans decide. Especially for consequential actions like merging or deleting content, the agent\'s output should always be a draft or recommendation --- never an automatic write-back. |
+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**4. Prompting for Small Models**

Most prompting advice is written for large models. Small models (1B--8B parameters) behave differently --- they are more literal, more prone to drift, and more sensitive to prompt structure. The techniques below are specifically optimised for models like gemma3:1b, llama3:8b, and similar.

**4.1 One Agent, One Job**

Do not write a system prompt that tries to make one agent do everything. A system prompt that lists ten possible tasks will produce inconsistent results on a small model. Define one clear role per agent and scope it tightly.

+------------------------------------------------------------------------------------------------------------+
| **❌ Too broad**                                                                                           |
|                                                                                                            |
| \"You are a helpful assistant that can summarise, translate, write code, classify, and answer questions.\" |
+------------------------------------------------------------------------------------------------------------+

+-----------------------------------------------------------------------------------------------------------------------------------------------+
| **✅ Well scoped**                                                                                                                            |
|                                                                                                                                               |
| \"You are a code reviewer. You receive Python functions and return structured feedback on correctness, style, and edge cases. Nothing else.\" |
+-----------------------------------------------------------------------------------------------------------------------------------------------+

**4.2 Keep System Prompts Short**

Small models can lose focus when system prompts are long. Every sentence in a system prompt should earn its place. A well-structured 10-line system prompt consistently outperforms a sprawling 50-line one on small models.

-   State the agent\'s role in one sentence

-   Define the input structure the agent should expect

-   List behavioural rules as a numbered list --- not prose

-   Specify output format constraints (IDs, no extra commentary, etc.)

**4.3 Replace Free Generation with Templates**

This is the single most impactful technique for small models. Instead of describing what good output looks like, give the model a template to fill in. Free generation is the enemy of consistency at low parameter counts.

+------------------------------------------------------------------------------------------------------------------------+
| **Principle**                                                                                                          |
|                                                                                                                        |
| Small models pattern-match more reliably than they reason. Give them a form to fill in, not a description of the form. |
+------------------------------------------------------------------------------------------------------------------------+

-   Provide a literal output template with labelled placeholders

-   Use tables with column headers the model fills cell by cell

-   Specify allowed values explicitly: \"Write one of: PASS, NEEDS WORK, or REVISE\"

-   Instruct the model to write nothing outside the template

**4.4 Use Numbered Steps, Not Prose Instructions**

Small models follow procedural instructions better than they interpret descriptive ones. Structure skill files as a sequence of explicit steps, each with a single decision to make.

+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **❌ Descriptive (inconsistent on small models)**                                                                                                                   |
|                                                                                                                                                                     |
| \"Review the insight for clarity, considering whether the statement is specific, whether the evidence is sufficient, and whether the argument is logically sound.\" |
+---------------------------------------------------------------------------------------------------------------------------------------------------------------------+

+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **✅ Procedural (consistent on small models)**                                                                                                                            |
|                                                                                                                                                                           |
| \"Step 1: Read the Statement. Ask: is it specific? Does it make one claim? Assign one verdict: PASS, NEEDS WORK, or REVISE. Write one sentence explaining your verdict.\" |
+---------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**4.5 Embed Concrete Examples in Skill Files**

Abstract criteria are hard for small models to apply consistently. Wherever you specify a quality standard, add a concrete bad example and a concrete good example directly in the skill file.

-   Bad/good pairs are more reliable than written criteria alone

-   Use the exact domain language the model will encounter in the data

-   Place examples immediately adjacent to the criterion they illustrate

**4.6 Define Verdict Logic Explicitly**

Do not ask a small model to weigh multiple factors and arrive at an overall judgement. Give it explicit decision rules instead.

+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Example of explicit verdict logic**                                                                                                                                   |
|                                                                                                                                                                         |
| \"If any section is REVISE → Overall is REVISE. If any section is NEEDS WORK and none are REVISE → Overall is NEEDS WORK. If all sections are PASS → Overall is PASS.\" |
+-------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**5. Guardrails**

Guardrails are constraints that prevent the agent from producing outputs that are wrong, unsafe, or inconsistent. For local agents, guardrails live in three places: the system prompt, the skill files, and the orchestrator code.

**5.1 Prompt-Level Guardrails**

These are instructions embedded in the system prompt or skill that constrain what the model can and cannot do.

  ------------------------ ------------------------------------------------------------------------------------------------
  **Guardrail type**       **Example instruction**

  Stay in scope            \"Only use information from the insight files provided. Do not add outside knowledge.\"

  No silent actions        \"Never rewrite or delete content. Only suggest changes and explain why.\"

  ID references            \"Always refer to insights by their ID (e.g. INS-001). Never refer to insights by title.\"

  Format lock              \"Do not add introductions, sign-offs, or commentary outside the output format.\"

  Defer to humans          \"Use language like \'suggested\', \'consider\', and \'worth reviewing\' --- never instruct.\"
  ------------------------ ------------------------------------------------------------------------------------------------

**5.2 Output Format Enforcement**

The most effective prompt-level guardrail is a rigid output template. When the model has a template to fill in, it has far less opportunity to hallucinate structure, add unsolicited commentary, or drift in tone.

-   Provide the full template, including headers and placeholder text

-   Specify exactly what goes in each field: \"One sentence.\" not \"Your notes.\"

-   Instruct the model explicitly: \"Do not add anything outside this format.\"

**5.3 Code-Level Guardrails**

Some guardrails belong in the orchestrator, not the prompt. These are structural constraints that do not depend on the model following instructions.

  --------------------------- -------------------------------------------------------------------------------------
  **Guardrail**               **Implementation**

  Validate insight IDs        Check that input IDs match files on disk before calling the model

  Bounded task types          Use an allowlist (e.g. argparse choices) so only known tasks can be run

  Read-only data              Never pass file write handles to the agent --- outputs go to a separate directory

  Surface model errors        Parse Ollama\'s error response body and surface the message, not just the HTTP code

  Output review before save   Consider a \--dry-run flag that prints output without saving, for review
  --------------------------- -------------------------------------------------------------------------------------

**5.4 Temperature and Sampling**

For tasks where format consistency matters more than creative variation --- such as structured reviews, verdicts, and summaries --- set temperature to 0 or close to it. This is one of the most reliable levers for consistent output on small models.

+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| **Recommendation**                                                                                                                                                                       |
|                                                                                                                                                                                          |
| Set temperature: 0 in your Ollama payload for clarity review, redundancy check, and any task with a fixed output schema. Reserve higher temperatures only for open-ended drafting tasks. |
+------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+

**6. File and Project Structure**

A consistent project structure makes agents easier to maintain, test, and hand off to others. The structure below emerged from practical use and reflects the three-layer architecture described in Section 3.

+-----------------------------------------------------------------------+
| project/                                                              |
|                                                                       |
| run.py \# CLI entry point                                             |
|                                                                       |
| agent/                                                                |
|                                                                       |
| orchestrator.py \# Loads skills, calls model, saves output            |
|                                                                       |
| system_prompt.txt \# Agent identity and global rules                  |
|                                                                       |
| skills/                                                               |
|                                                                       |
| skill_task_one.md \# Instructions for task type A                     |
|                                                                       |
| skill_task_two.md \# Instructions for task type B                     |
|                                                                       |
| data/ \# Input files (read-only to agent)                             |
|                                                                       |
| outputs/ \# Agent outputs (never input files)                         |
+-----------------------------------------------------------------------+

-   Keep input data and agent outputs in separate directories

-   Name skill files descriptively: skill_clarity_review.md, not skill1.md

-   Store the system prompt as a plain text file, not hardcoded in Python

-   Version-control skills alongside code --- they are part of the system

**7. Testing and Iteration**

Prompt engineering for small models is empirical. Expect to iterate. The following practices make iteration faster and more systematic.

**7.1 Design Test Cases Into Your Data**

Create input files that are intentionally designed to test specific behaviours. Do not rely only on real-world data for testing.

-   Create a weak/vague input to verify the model correctly identifies problems

-   Create a strong/clean input to verify the model correctly awards passing verdicts

-   Create a pair of overlapping inputs to verify redundancy detection

-   Label test files clearly so the team knows they are for testing

**7.2 Isolate Changes**

When iterating on prompts, change one thing at a time. The most common mistake is rewriting an entire skill file after one bad output. Change the specific instruction that failed, re-run the same test input, and compare.

**7.3 Watch for These Failure Modes**

  -------------------------------------------------- --------------------------------------------------------------------
  **Failure mode**                                   **Likely cause and fix**

  Adds commentary outside the format                 Add: \"Do not add anything outside this format.\" to the skill

  Ignores verdict rules                              Replace prose criteria with explicit if/then logic

  Slips into research language in executive output   Add a do/don\'t example directly adjacent to the writing rule

  Confuses insight IDs                               Add: \"Always refer to insights by their ID\" to the system prompt

  Inconsistent verdict across runs                   Lower temperature to 0; simplify the decision criteria

  Ignores part of the template                       Break the template into smaller steps; add \"Complete every row\"
  -------------------------------------------------- --------------------------------------------------------------------

**8. Summary Checklist**

Use this checklist when setting up a new local agent.

**System Prompt**

-   Role defined in one sentence

-   Input structure described concisely

-   Behavioural rules listed as numbered items

-   Output constraints stated explicitly

-   Length under 15 lines

**Skill Files**

-   Instructions written as numbered steps, not prose

-   Each step has one decision to make

-   Verdict options listed explicitly with definitions

-   Output template included with placeholders

-   Concrete bad/good examples included for key criteria

-   \"Do not add anything outside this format\" stated at the end

**Orchestrator**

-   Skill loaded dynamically based on task type

-   Task types validated against an allowlist

-   Input file IDs validated before model call

-   Outputs written to a separate directory from inputs

-   Error response body parsed and surfaced to the user

-   Temperature set to 0 for structured output tasks

**Testing**

-   Weak input file created for negative testing

-   Strong input file created for positive testing

-   Changes made one at a time during iteration

-   Outputs reviewed before being committed back to the repository

*These practices were derived from hands-on experimentation. Treat them as a starting point, not a fixed standard --- every model and use case will require some adjustment.*
