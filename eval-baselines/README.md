# Reviewed eval baselines

Raw model runs stay under the gitignored `eval-runs/`. A baseline is promoted here only after its outputs, judge reasoning, isolation, and fingerprint manifest have been reviewed.

A promoted baseline is a directory containing:

```text
eval-baselines/<name>/
├── meta.json          # run configuration and source revision
├── fingerprints.json  # per-case content/runner/config fingerprints
├── benchmark.json     # compliance aggregates, or triggers.json
├── errors.json        # recorded run errors from the source run (may be [])
└── review.json        # reviewer, date, source run, and notes
```

`review.json` has this shape:

```json
{
  "schema_version": 1,
  "reviewed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "reviewed_by": "name",
  "source_run": "eval-runs/iteration-name",
  "notes": "What was checked and why this result is trustworthy."
}
```

Check a raw run or promoted baseline without making model calls:

```sh
python3 scripts/eval-status.py eval-runs/iteration-name
python3 scripts/eval-status.py eval-baselines/<name> --check
```

A baseline should not be promoted until the independent-judge and held-out-case work is complete. Where a promotion knowingly carries flaws (for example fingerprints that read STALE because the runner changed after the run, or arms flagged by the retry-contamination audit), `review.json` states them explicitly rather than burying them in commit messages. Older exploratory aggregates remain historical only.
