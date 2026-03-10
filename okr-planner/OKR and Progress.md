# Q1 2025 OKRs

## Objective 1: Increase Product Adoption
**Owner:** Sarah
**Due:** March 31

### KR1: Reach 500 active users
- Target: 500
- Current: 312 (62%)
- Last update: Feb 14
- Notes: Onboarding flow rework shipped Feb 10. Activation rate improved from
  18% to 24% but volume hasn't caught up yet. Marcus's enterprise deals could
  add 40–60 users if they close this month. Need data from Priya's team to
  confirm whether the onboarding change is holding.

### KR2: Reduce churn to < 5%
- Target: < 5%
- Current: 7.2%
- Last update: Feb 10
- Notes: Retention campaign not started — Sarah is backlogged on support
  tickets from the onboarding rollout. Needs sign-off from Marcus on the
  campaign budget before launch. Legal flagged that the discount offer in
  the campaign draft needs review before it goes out.

### KR3: Achieve NPS score of 45+
- Target: 45
- Current: 41
- Last update: Feb 1
- Notes: Last survey had 18% response rate — too low to be reliable. Next
  survey planned for end of Feb. Unclear whether the onboarding improvements
  have changed sentiment yet. No action taken on negative verbatims from
  the last survey.

---

## Objective 2: Accelerate Revenue Growth
**Owner:** Marcus
**Due:** March 31

### KR1: Close 10 new enterprise deals
- Target: 10
- Current: 3 closed (30%)
- Last update: Feb 15
- Notes: 6 deals in active negotiation. 2 are stalled — both waiting on Legal
  to approve custom contract terms. Legal's current SLA is 3 weeks and both
  were submitted 2 weeks ago. Pipeline needs 1 new qualified lead per week to
  hit target if all 6 close. SDR team is underperforming on outbound volume.

### KR2: Grow MRR to $120k
- Target: $120,000
- Current: $89,000 (74%)
- Last update: Feb 15
- Notes: On track only if the 6 enterprise deals close on schedule. Self-serve
  MRR has plateaued at $51k for 3 months — no growth initiative targeting
  self-serve segment currently active. If enterprise deals slip to April,
  MRR will land around $95k.

### KR3: Launch partner referral program
- Target: Launched and generating leads
- Current: 0% — not started
- Last update: Jan 20
- Notes: Completely blocked on Legal. Partner agreement template submitted
  Jan 15 — no response in 5 weeks. Marcus has not escalated. Without the
  template approved, no partner conversations can begin. Even if unblocked
  today, launch is 4–6 weeks away minimum.

---

## Objective 3: Improve Engineering Velocity
**Owner:** Priya
**Due:** March 31

### KR1: Reduce average PR review time to < 24 hours
- Target: < 24 hours
- Current: 31 hours (target not met)
- Last update: Feb 13
- Notes: Dedicated review slots introduced Tues/Thurs — avg dropped from
  38h to 31h. Biggest bottleneck is 2 senior engineers who handle 60% of
  reviews but are also on-call. Need to distribute review load more evenly.
  No tooling in place to track review time automatically — data is manual.

### KR2: Achieve 80% test coverage across core services
- Target: 80%
- Current: 67% (target not met)
- Last update: Feb 12
- Notes: Auth service at 91%, payments service at 48% — payments is the
  critical gap. Payments engineer is new and unfamiliar with the testing
  framework. Coverage tooling reports are run manually every 2 weeks —
  no automated threshold enforcement in CI/CD yet.

### KR3: Deploy CI/CD pipeline for all services
- Target: 8 of 8 services
- Current: 5 of 8 services (62%)
- Last update: Feb 10
- Notes: Remaining 3 services have legacy Ruby dependencies that conflict
  with the current pipeline config. Spike scheduled Feb 20 to assess
  migration effort. Estimated 2–3 weeks of work per service if migration
  is required. External vendor may need to be involved for one service.
