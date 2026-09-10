---
name: profile-pipeline
description: >
  Profile a slow shell pipeline to find which stage is the bottleneck and speed it
  up. Use when a piped command (grep | sort | awk, tar | gzip, find | xargs, curl |
  jq, docker build chains, log-processing one-liners) takes too long, when asked
  why a pipeline is slow, which stage costs the most, or how to make it faster.
---

# Profile pipeline

Find the slow stage first, fix second. Guessing which stage is slow is wrong most
of the time — measure before changing anything.

## Workflow

1. **Reproduce with a baseline.** Run the whole pipeline once under `time`,
   discarding output so paging doesn't pollute the measurement. Done when you
   have one `real/user/sys` number for the full pipeline.
   ```sh
   bash -c 'set -o pipefail; time (<pipeline> > /dev/null)'
   ```
2. **Bisect by prefix.** Time growing prefixes (`stage1`, `stage1 | stage2`,
   …), each to `/dev/null`. The stage whose prefix jumps is the bottleneck.
   Done when each stage has a marginal cost (prefix_N minus prefix_N-1).
   ```sh
   time (seq 100000 | grep 5 > /dev/null)
   time (seq 100000 | grep 5 | sort > /dev/null)
   ```
3. **Work on a sample.** Reproduce on `head -n` subset for fast iteration
   (confirm the bottleneck still shows at small N). Never tune against full
   production data until the fix is picked.
4. **Classify the bottleneck, then fix the class:**
   - CPU-bound (`user` dominates: `sort`, `gzip -9`, `jq`, `awk`): fewer bytes
     through it (filter earlier with `grep`/`head`), lower cost flags
     (`gzip -1`, `sort -S`), or parallelize (`xargs -P`, `sort --parallel`).
   - I/O-bound (`real` >> `user+sys`: network, disk, `curl`, `tar`): overlap
     stages, compress later, cache the download.
   - Buffering/serialization (fast alone, slow piped; `grep`/`awk`/`sed`
     waiting on blocks): unbuffer with `stdbuf -oL -i0` or the tool's own
     line-buffered flag (`grep --line-buffered`, `sed -u`, `awk` with
     `fflush()`), and drop useless `cat`.
   - Optional live view: if `pv` is installed (`command -v pv`), insert
     `pv -t` between stages to watch throughput per segment.
5. **Re-measure and report.** Re-run step 1 after the fix on the same input.
   Done when you can quote before/after `real` numbers from identical runs.

## Guardrails

- Keep `set -o pipefail` on every timed run so a failure inside the pipe
  fails loudly instead of timing a truncated stream.
- Time at least twice; ignore the first run if caches are cold.

## Output

The bottleneck stage with its marginal cost, the fix applied (or proposed),
and before/after `real` timings from identical inputs. If two stages tie,
name both and fix the earlier one first.

Pairs with `validate-results` when the pipeline produces numbers worth
re-checking after the fix.

---

Created during write-skill eval scoring, reviewed and adopted into this repo.
