# Skill: trace-analyze

Analyze recent execution traces for failure patterns.

## When to Use
- After task failures to understand root causes
- Before running evolution to identify optimization targets
- When the user asks why something went wrong

## Steps
1. Load recent execution traces from ~/.dolios/traces/
2. Filter by outcome (failures, partial completions)
3. Identify common failure patterns:
   - Tool selection errors (wrong tool for the task)
   - Network policy blocks (endpoint not allowed)
   - Timeout issues (commands taking too long)
   - Inference errors (model hallucinations, refusals)
4. Correlate failures with specific skills and tools
5. Rank patterns by frequency and impact
6. Suggest specific improvements

## Output Format
- Traces analyzed: N (date range)
- Success rate: X%
- Top failure patterns (ranked):
  1. Pattern description — frequency — affected skills/tools
  2. ...
- Recommendations: concrete improvement actions
