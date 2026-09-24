# Decision log

## DEC-001: Install missing pi packages with explicit `pi install`, not `pi update --extensions`
- **Date:** 2026-09-24
- **Status:** decided
- **Context:** Fresh-machine setup where `settings.json` declares the seven packages but the `npm/` tree is empty. Both the pi README and the root runbook say pi installs missing packages on startup and that `pi list` + `pi update --extensions` confirm the set. On this machine `pi update --extensions` printed "Updated packages" but silently did nothing: it reconciles already-downloaded packages and does not fetch ones that are declared yet never downloaded, and `pi list` kept showing "No packages installed". Burned a few cycles assuming the manifest or install was broken.
- **Options considered:**
  - Run `pi update --extensions` and trust the runbook — fails silently on never-downloaded packages.
  - Start an interactive `pi` session to trigger the on-startup install — heavier, needs a working auth/model setup first.
  - Run `pi install <spec>` for each declared spec — idempotent: re-declaring an already-listed spec does not duplicate the `packages[]` entry, it only fetches the bytes into the (untracked) `npm/` tree.
- **Decision:** On a machine where `pi list` shows fewer packages than `settings.json` declares, run `pi install` for each missing spec, then `pi update --extensions` as usual. Worth fixing the runbook's step 3 wording so it says this instead of implying startup/update handles it.
- **Consequences:** New-machine installs need the per-spec loop until the runbook is updated; `pi install` on an already-declared spec is safe to run blindly. Follow-up: reword the post-link step in AGENTS.md and pi/README.md.
