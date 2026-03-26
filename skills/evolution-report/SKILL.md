# Skill: evolution-report

Show self-evolution pipeline status and recent optimizations.

## When to Use
- User asks about self-improvement status
- After an evolution cycle completes
- When reviewing agent performance over time

## Steps
1. Check evolution pipeline status (idle/running/completed)
2. List recent evolution runs with outcomes
3. Show which skills/prompts were optimized and by how much
4. Report any pending PRs from the evolution pipeline
5. Show constraint gate results from the last run
6. Recommend next evolution targets based on trace analysis

## Output Format
- Pipeline status: idle/running/completed
- Last run: date, target, outcome
- Recent improvements: skill/prompt name, improvement %
- Pending PRs: count and links
- Recommended targets: 2-3 suggestions with rationale
