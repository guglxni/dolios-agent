# Skill: model-switch

Switch inference provider with awareness of sandbox routing.

## When to Use
- User wants to change the model or provider
- Current provider is unavailable or rate-limited
- Task type would benefit from a different model's strengths

## Steps
1. List available providers (those with valid API keys and sandbox policy access)
2. If user specified a provider: validate it's available and policy-allowed
3. If auto-selecting: use inference router to pick optimal provider for task type
4. Update the inference route configuration
5. Verify the new provider responds (quick health check)
6. Confirm the switch to the user

## Output Format
- Previous: provider/model
- Switched to: provider/model
- Reason: user preference / auto-selected for [task_type]
