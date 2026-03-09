---
name: quota-monitoring-handoff
description: Monitor Codex or AMP session quotas and hand off orchestration when limits are near. Use when a quota-limited orchestrator must transfer control to another LLM.
---

# Quota Monitoring and Handoff

Note: Codex-led sessions often skip this. Use only if the current orchestrator has a quota limit.

## Arguments
- session: tmux session name.
- window: orchestrator window (often Codex or AMP).
- threshold: percentage to trigger a handoff (default 93).
- interval_sec: watchdog interval in seconds.
- handoff_target: LLM that will take over (default Amp).
- handoff_file: path to a handoff summary file.

## Objectives
- Detect when a quota threshold is reached.
- Write a compact handoff summary.
- Notify the next orchestrator and confirm they are active.

## Steps
1) Read the current quota in the orchestrator window.
2) If the threshold is reached, write a handoff summary file.
3) Notify the target LLM with the handoff instructions.
4) Verify the target LLM is active and has read the summary.

## Examples

Check quota once:

```bash
scripts/check-session-quota.sh $SESSION codex 93
```

Run the watchdog:

```bash
nohup scripts/quota-watchdog.sh $SESSION codex 93 30 &
```

## Resources
- `scripts/check-session-quota.sh`: single quota check.
- `scripts/quota-watchdog.sh`: continuous monitoring.
- `scripts/auto-handoff.sh`: one-shot handoff (generic).
- `scripts/auto-handoff-to-amp.sh`: compatibility wrapper for Codex -> AMP handoff.
- `assets/handoff-template.md`: handoff summary template.
- `references/handoff-procedure.md`: detailed steps and thresholds.
