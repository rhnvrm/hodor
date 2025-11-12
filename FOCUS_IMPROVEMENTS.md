# Agent Focus Improvements

## Problem Statement

The agent was reviewing the **entire codebase** instead of just the PR's changed files, leading to:
- Incorrect findings about files not even in the PR
- False positives about "branch sync" issues (files deleted, dependencies downgraded)
- Very slow reviews (checking hundreds of files instead of 2-3 changed files)
- Wasted tokens and cost

**Example**: PR only changed `cmd/dump/hub.go` and `pkg/batch/batch.go`, but agent reported issues in `cmd/dump/store/redis.go`, `pkg/utils/utils.go`, and other unrelated files.

## Root Cause

The prompt was too vague:
- Said "use `gh pr diff`" but didn't enforce it as MANDATORY FIRST STEP
- Didn't explicitly restrict agent to ONLY reviewing files in the diff
- Agent interpreted "review the PR" as "review the entire branch state vs main"

## Solution

### 1. **Rewrite Prompt with Strict Focus** (`hodor/prompts/pr_review_prompt.py`)

Made it crystal clear with a 3-step process:

**STEP 1: Get the Diff (MANDATORY FIRST STEP)**
```bash
Run this command FIRST and ONLY review files shown:
gh pr diff {pr_number}  # or glab mr diff
```

**STEP 2: Review ONLY Those Files**
```
CRITICAL RULES:
- ✅ ONLY review files that appear in the diff from Step 1
- ✅ ONLY analyze the actual code changes (+ and - lines in the diff)
- ❌ NEVER review files not in the diff
- ❌ NEVER flag "files will be deleted when merging" - that's just outdated branch
- ❌ NEVER flag "dependency version downgrade" - that's just branch not rebased
- ❌ NEVER compare entire codebase to main - DIFF ONLY

Example:
- Diff shows: cmd/dump/hub.go and pkg/batch/batch.go changed
- You review: ONLY cmd/dump/hub.go and pkg/batch/batch.go
- You ignore: ALL other files (even if you see them in the repo)
```

**STEP 3: Analyze Each Changed File**
```
For each file in the diff:
1. Read the diff to see what changed
2. Look for bugs in the NEW/MODIFIED code only
3. Ignore pre-existing code unless the PR breaks it
```

### 2. **Simplified Metrics** (Always Show)

Removed 3rd party observability docs (Laminar, Honeycomb, etc.) - not needed.

Now **every review** shows concise metrics:
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

Changes:
- Metrics now print **always** (not just with `-v`)
- Added **Review Time** to track performance
- Removed verbose OpenTelemetry tracing docs
- Simplified output (no cache writes, latency in verbose only)

### 3. **Expected Improvements**

With these changes, for a PR that changes 2 files:

**Before:**
- Agent checks 50+ files
- Flags "branch sync" issues
- Takes 10-15 minutes
- Costs $2-3 per review

**After:**
- Agent checks ONLY the 2 changed files
- No false positives about branch state
- Takes 1-3 minutes
- Costs $0.10-0.50 per review (5-10x cheaper)

## Testing the Improvements

Test with a real PR:
```bash
hodor https://gitlab.com/your/repo/-/merge_requests/123 -v
```

**What to verify:**
1. Agent runs `gh pr diff` or `glab mr diff` FIRST
2. Agent explicitly lists the changed files
3. Agent ONLY reviews those files
4. No mentions of "files will be deleted" or "dependency downgrade"
5. Review completes in 1-3 minutes (not 10-15)
6. Metrics show at the end

## Additional Benefits

1. **Faster reviews** - Only checking what actually changed
2. **Lower cost** - Fewer tokens used
3. **Better accuracy** - No false positives from branch sync issues
4. **Easier debugging** - Clear metrics show performance

## Files Changed

1. `hodor/prompts/pr_review_prompt.py` - Complete prompt rewrite with 3-step process
2. `hodor/agent.py` - Always print metrics, add review time
3. `README.md` - Simplified metrics section
4. `OBSERVABILITY.md` - Deleted (not needed)

## Next Steps

If agent still reviews unrelated files:
1. Check if it's running the diff command first (look for `gh pr diff` in logs with `-v`)
2. Verify the diff command output shows the correct files
3. Ensure agent doesn't "explore" the codebase before reading the diff
4. Consider adding explicit file list to the prompt context (pre-fetch diff and include it)

## Additional Fixes (Post-Initial Release)

### Git Pager Issue (Fixed)
**Problem**: Agent getting stuck in interactive git pager (less/more), unable to capture output.
**Solution**: Added explicit instructions to disable pager:
- Set `export GIT_PAGER=cat` at start of review
- Use `git --no-pager diff` for all git commands
- Updated all prompt examples to include `--no-pager` flag

### Git Diff Syntax Issue (Fixed)
**Problem**: Using two-dot diff (`origin/main..HEAD`) shows ALL differences including changes already on main, causing false positives about "files being deleted" or "dependencies downgraded" when branch is not rebased.
**Solution**: Use three-dot diff (`origin/main...HEAD`) to show ONLY changes introduced on the source branch since divergence.
**Difference**:
- `..` (two dots) = All commits from main to HEAD (includes main changes not in source)
- `...` (three dots) = Changes since common ancestor (excludes main changes)
**Result**: Agent now reviews ONLY actual PR changes, no false positives from stale branches.

### Extended Thinking Default (Fixed)
**Problem**: OpenHands SDK defaults to `reasoning_effort="high"` and `extended_thinking_budget=200000`, causing slow reviews (10-15 min).
**Solution**: Explicitly set `reasoning_effort="none"` unless user passes `--reasoning-effort` flag.
**Result**: Fast reviews (1-3 min) by default, opt-in for deep thinking when needed.

### Professional Review Guidelines (Added)
**Added comprehensive review criteria:**
- Enhanced bug criteria (9-point checklist)
- Mandatory Trigger/Impact/Proof for every finding
- Refined priority levels (P0=universal, P1=conditional)
- Professional comment guidelines (brief, matter-of-fact)
- Overall verdict section (✅ correct | ❌ blocking issues)
