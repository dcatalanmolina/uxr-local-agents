# Task: Redundancy Check

You will compare a set of insights and identify any overlap. Follow the steps below exactly.

---

## Step 1: Compare Statements

Read the Statement section of each insight. For every pair of insights, ask:
- Do they make the same claim, even if worded differently?
- Does one statement describe a specific case of another?

If yes → mark as HIGH OVERLAP.

## Step 2: Compare Evidence

Read the Evidence section of each insight. For every pair, ask:
- Do they reference the same study, session, or data source?
- Do they describe the same user behavior?

If yes → mark as PARTIAL OVERLAP.

## Step 3: Look for Thematic Clusters

Look at all insights together. Ask:
- Do three or more insights point to the same underlying problem?

If yes → mark as THEMATIC CLUSTER and give the theme a short name.

---

## Verdict Definitions

- HIGH OVERLAP: The two insights say the same thing. Suggest merging.
- PARTIAL OVERLAP: The two insights share evidence or behavior but have different claims. Suggest cross-referencing.
- THEMATIC CLUSTER: Three or more insights share a theme. Suggest a synthesis insight.
- NO ISSUES: No overlap found.

---

## Output Format

Use this exact format. Do not add anything outside this format.
If a section has no findings, write "None found." under it.

**Redundancy Report**

### High Overlap
[INSIGHT ID] + [INSIGHT ID] — [One sentence explaining the overlap.]
Suggested action: Merge. Keep [INSIGHT ID] as primary.

### Partial Overlap
[INSIGHT ID] + [INSIGHT ID] — [One sentence explaining the shared evidence or behavior.]
Suggested action: Add a cross-reference note to both insights.

### Thematic Clusters
Theme: [Short theme name]
Insights: [INSIGHT ID], [INSIGHT ID], [INSIGHT ID]
Suggested action: Consider creating a synthesis insight that covers this theme.

### Summary
[One or two sentences describing the most important redundancy to address, or confirming no action is needed.]
