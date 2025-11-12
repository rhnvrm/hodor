# Hodor 🚪

> AI code review agent that finds bugs, not style issues.

**Automated PR reviews for GitHub & GitLab** • Runs in CI/CD • Posts comments automatically • Fast (1-3 min avg)

## What It Does

Reviews your pull requests and finds:
- **Bugs**: Race conditions, null derefs, logic errors, resource leaks
- **Security**: SQL injection, XSS, auth bypasses, secrets in code
- **Performance**: N+1 queries, O(n²) algorithms, memory leaks

**Not**: Code style, formatting, or subjective opinions.

## Quick Start

```bash
# Install
pip install uv
git clone https://github.com/mr-karan/hodor
cd hodor && uv sync

# Authenticate
gh auth login        # GitHub
glab auth login      # GitLab (optional)

# Set API key
export ANTHROPIC_API_KEY=sk-ant-your_key_here

# Review a PR
uv run hodor https://github.com/owner/repo/pull/123

# Auto-post review comment
uv run hodor https://github.com/owner/repo/pull/123 --post
```

**Docker**:
```bash
docker run --rm \
  -e ANTHROPIC_API_KEY=your_key \
  ghcr.io/mr-karan/hodor:latest \
  https://github.com/owner/repo/pull/123
```

## How It Works

1. Clones repo & checks out PR branch
2. AI agent runs `git diff`, `grep`, analyzes changes
3. Generates markdown review with file:line references
4. Posts comment (if `--post` flag used)

Uses [OpenHands SDK](https://github.com/OpenHands/agent-sdk) for autonomous agent execution.

## Installation

### Docker (Recommended)

```bash
docker pull ghcr.io/mr-karan/hodor:latest

docker run --rm \
  -e ANTHROPIC_API_KEY=your_key \
  ghcr.io/mr-karan/hodor:latest \
  https://github.com/owner/repo/pull/123
```

### From Source

```bash
# Install dependencies
pip install uv
git clone https://github.com/mr-karan/hodor
cd hodor && uv sync

# Authenticate
gh auth login        # GitHub
glab auth login      # GitLab

# Set API key
export ANTHROPIC_API_KEY=sk-ant-your_key_here

# Run
uv run hodor https://github.com/owner/repo/pull/123
```

## Usage

### Basic Review
```bash
# Review and print to console
hodor https://github.com/owner/repo/pull/123

# Auto-post as PR comment
hodor https://github.com/owner/repo/pull/123 --post

# Verbose mode (see agent activity)
hodor https://github.com/owner/repo/pull/123 -v
```

### GitLab & Self-Hosted
```bash
# GitLab.com
hodor https://gitlab.com/owner/project/-/merge_requests/123 --post

# Self-hosted GitLab (auto-detected from URL)
hodor https://gitlab.yourcompany.com/team/project/-/merge_requests/42 --post
```

### Custom Options
```bash
# Use different model
hodor https://github.com/owner/repo/pull/123 --model gpt-5

# Custom prompt
hodor https://github.com/owner/repo/pull/123 \
  --prompt "Focus only on security issues"

# Reuse workspace (faster for multiple PRs from same repo)
hodor https://github.com/owner/repo/pull/123 --workspace /tmp/workspace
hodor https://github.com/owner/repo/pull/124 --workspace /tmp/workspace  # Reuses!
```

### Extended Thinking (Slow!)
```bash
# WARNING: Takes 10-15 minutes (vs 1-3 min default)
hodor https://github.com/owner/repo/pull/123 --reasoning-effort high
```

## CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/hodor.yml
name: Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    container: ghcr.io/mr-karan/hodor:latest
    steps:
      - name: Run review
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          hodor "https://github.com/${{ github.repository }}/pull/${{ github.event.pull_request.number }}" --post
```

Set `ANTHROPIC_API_KEY` in Settings → Secrets. `GITHUB_TOKEN` is auto-provided.

### GitLab CI
```yaml
# .gitlab-ci.yml
hodor-review:
  image: ghcr.io/mr-karan/hodor:latest
  stage: test
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  script:
    - hodor "${CI_PROJECT_URL}/-/merge_requests/${CI_MERGE_REQUEST_IID}" --post
  allow_failure: true
```

Set `GITLAB_TOKEN` and `ANTHROPIC_API_KEY` in Settings → CI/CD → Variables.

See [AUTOMATED_REVIEWS.md](./AUTOMATED_REVIEWS.md) for advanced setup.

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| `--model` | `claude-sonnet-4-5` | LLM model |
| `--temperature` | `0.0` | Sampling temperature (0=deterministic) |
| `--reasoning-effort` | (off) | Extended thinking: `low`/`medium`/`high` (slow!) |
| `--workspace` | (temp) | Reuse workspace dir for multiple PRs |
| `--post` | off | Auto-post review as PR comment |
| `-v` | off | Verbose logging |

**Environment Variables:**
- `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` - LLM API key (required)
- `GITHUB_TOKEN` - GitHub auth (use `gh auth login`)
- `GITLAB_TOKEN` - GitLab auth (use `glab auth login`)
- `GITLAB_HOST` - For self-hosted GitLab

**Defaults:**
- Model: Claude Sonnet 4.5
- Temperature: 0.0 (deterministic)
- Reasoning: Disabled (fast, 1-3 min per review)
- Workspace: Temp dir (cleaned up after)

**Supported Models:**
- Anthropic: `claude-sonnet-4-5`, `claude-opus-4`
- OpenAI: `gpt-5`, `gpt-4-turbo`, `o3-mini`
- Google: `gemini-2.5-pro`, `gemini-2.5-flash`
- Custom: Any OpenAI-compatible API (set `LLM_BASE_URL`)

## Metrics

Every review shows detailed metrics:
```
============================================================
📊 Token Usage Metrics:
  • Input tokens:       3,820,000
  • Output tokens:      23,980
  • Cache hits:         3,650,000 (95.5%)
  • Total tokens:       3,852,130

💰 Cost Estimate:      $2.0948
⏱️  Review Time:        2m 34s
============================================================
```

Cache hit rate > 90% = efficient! Use `-v` for detailed logging.

## Contributing

Contributions welcome!

## License

MIT
