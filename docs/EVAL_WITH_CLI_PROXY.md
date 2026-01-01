# Running Hodor with CLI Proxy (Claude Max)

Use Claude Max subscription instead of per-token API billing for cost-free evaluations.

## Prerequisites

1. **CLIProxyAPI** running on `localhost:8317`
   - Start with: `cliproxyapi --port 8317`

2. **Claude Max subscription** with Claude Code authenticated

3. **GitLab token** for private repos (if using self-hosted GitLab)

## Quick Start

```bash
# Required environment variables
export LLM_API_KEY=dummy                    # Proxy ignores this
export LLM_BASE_URL=http://localhost:8317/v1
export GITLAB_HOST=your-gitlab.example.com  # For self-hosted GitLab
export GITLAB_TOKEN=your-token              # GitLab API token

# Force subprocess terminal (avoids tmux issues)
export OPENHANDS_FORCE_SUBPROCESS_TERMINAL=1

# Run hodor
uv run hodor "https://your-gitlab.example.com/owner/repo/-/merge_requests/123" \
  --model openai/claude-haiku-4-5-20251001 \
  --lite-model openai/claude-haiku-4-5-20251001 \
  --workspace /path/to/local/clone
```

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `--model` | `openai/claude-haiku-4-5-20251001` | Prefix with `openai/` for OpenAI-compatible proxy |
| `--lite-model` | Same as model | For worker subagents |
| `--workspace` | Local path | Reuse existing clone, skip network ops |

## Available Models

The proxy supports any Claude model via OpenAI-compatible format:

```
openai/claude-haiku-4-5-20251001     # Fast, cheap
openai/claude-sonnet-4-5-20250514    # Balanced
openai/claude-opus-4-5-20251101      # Highest quality
```

## Workflow: Eval Loop

```bash
#!/bin/bash
# eval-loop.sh

EVAL_DIR=/tmp/hodor-eval
MR_URL="https://example.com/owner/repo/-/merge_requests/72"
WORKSPACE=/path/to/local/clone

mkdir -p $EVAL_DIR

OPENHANDS_FORCE_SUBPROCESS_TERMINAL=1 \
GITLAB_TOKEN=$GITLAB_TOKEN \
LLM_API_KEY=dummy \
LLM_BASE_URL=http://localhost:8317/v1 \
GITLAB_HOST=example.com \
uv run hodor "$MR_URL" \
  --model openai/claude-haiku-4-5-20251001 \
  --lite-model openai/claude-haiku-4-5-20251001 \
  --workspace "$WORKSPACE" \
  2>&1 | tee "$EVAL_DIR/run-$(date +%Y%m%d-%H%M%S).log"
```

## Metrics to Track

| Metric | How to Extract |
|--------|----------------|
| Duration | `Review Time: Xm Ys` in output |
| Tokens | `Total tokens: N` in output |
| Cost | Always $0.00 with proxy |
| Findings | Count P0/P1/P2/P3 in output |

## Troubleshooting

### "command too long" (tmux error)
```bash
export OPENHANDS_FORCE_SUBPROCESS_TERMINAL=1
```

### "text content blocks must be non-empty"
Fixed in hodor - review content is captured before error.
This is an OpenHands SDK quirk after finish tool.

### Auth errors on GitLab
Ensure `GITLAB_TOKEN` is set.

### Proxy not responding
Check CLIProxyAPI is running:
```bash
curl http://localhost:8317/v1/models
```

## Comparison: CLI Proxy vs Direct API

| Aspect | CLI Proxy | Direct API |
|--------|-----------|------------|
| Cost | $0 (Max subscription) | Per token |
| Speed | Similar | Similar |
| Rate limits | Claude Code limits | API limits |
| Auth | OAuth via Claude Code | API key |

## Development Notes

Changes made to support CLI proxy:

1. **`workspace.py`**: Skip clone when `--workspace` is an existing repo
2. **`cli.py`**: Read `LLM_BASE_URL` from environment
3. **`agent.py`**: Pass `base_url` to OpenHands agent
4. **`agent.py`**: Capture review even if conversation errors after finish
