# Freeze checklist — OSF pre-registration (after MD1, 2026-06-17)

Step-by-step to lock the live prediction. The **scientific value is the timestamp**: the model,
predictions, and scoring rule must be registered *before* MD2/MD3 are played. Everything technical
is prepared; the OSF registration itself is a manual step you perform on osf.io (I cannot post there).

---

## 0. Pre-flight (state to confirm before freezing)

- [ ] `data/draw_2026.json` holds **all 24 MD1 results** and groups are positionally correct
      (verified 2026-06-17; Group J reordered). MD2/MD3 are unplayed.
- [ ] Test suite green: `uv run python -m pytest -q`.
- [ ] Working tree clean: `git status` (commit any pending changes first).
- [ ] `PREREGISTRATION.md` reflects the **after-MD1** window (§6) and the official bracket (§3).

## 1. Generate the frozen prediction artifact (the registered predictions)

```bash
uv run python scripts/run_r4_named.py --bracket official --model elo \
    --snapshots 400 --inner 150 --margin 0.05 --out results/r4_freeze_elo.json
uv run python scripts/run_r4_named.py --bracket official --model poisson \
    --snapshots 400 --inner 150 --margin 0.05 --out results/r4_freeze_poisson.json
```

The **registered prediction set** (PREREGISTRATION §5): MD3 matches with P(manipulable) ≥ 0.50
under **both** models (the robust set), plus teams with P(cross_group) ≥ 0.20. These come straight
from the two artifacts; record them in RESULTS R11.

## 2. Commit the freeze (creates the immutable hash)

```bash
git add data/draw_2026.json results/r4_freeze_*.json RESULTS.md PREREGISTRATION.md
git commit -m "FREEZE: pre-registered MD3 manipulability predictions (after MD1, 2026-06-17)"
git push
git rev-parse HEAD          # <- this is the FREEZE COMMIT HASH
git tag freeze-2026-06-17 && git push --tags   # optional, human-friendly handle
```

Tag + push **before** registering, so the OSF record can point at an existing public commit.

## 3. Create the OSF registration (manual, on osf.io)

1. Sign in at <https://osf.io> → **Create new project** ("WC2026 manipulability — pre-registration").
2. In the project, **Add-ons / link the GitHub repo** (or upload `PREREGISTRATION.md` +
   `results/r4_freeze_elo.json` + `results/r4_freeze_poisson.json` directly as files).
3. Left sidebar → **Registrations** → **New registration** → choose the
   **"OSF Preregistration"** (or **"Open-Ended Registration"**) template.
4. In the registration form, paste / attach:
   - the full text of `PREREGISTRATION.md`,
   - the **freeze commit hash** from step 2 and the GitHub URL at that commit, e.g.
     `https://github.com/datasith/world-cup-2026/tree/<hash>`,
   - the two frozen artifact files (the named predictions).
5. Set an **embargo** only if you want it private until publication; otherwise register public so
   the timestamp is immediately verifiable.
6. Submit. OSF issues a **registration DOI** (e.g. `10.17605/OSF.IO/XXXXX`) and a frozen timestamp.

## 4. Record the identifiers back in the repo

Edit the `PREREGISTRATION.md` §0 header:
```
**Freeze commit:** <hash>  ·  **OSF DOI:** 10.17605/OSF.IO/XXXXX
```
```bash
git add PREREGISTRATION.md && git commit -m "Record OSF DOI + freeze hash" && git push
```
(This commit comes *after* the freeze; it only annotates, it does not change predictions.)

## 5. After MD3 (~late June) — scoring, not part of the freeze

- Add the real MD3 results to `data/draw_2026.json`.
- Score the primary endpoint (H1/H2, behaviour-independent) and the secondary passivity endpoint
  per PREREGISTRATION §7 (composite index, BH-FDR; behavioural endpoint descriptive if realized
  manipulable matches < 3).

---

### Notes / caveats to keep visible
- Freezing after MD1 means **MD2 and MD3 are both unobserved** — predictions are a genuine
  two-matchday-ahead forecast (stronger anti-leakage; wider intervals). Disclosed in §6.
- The OSF DOI is what reviewers cite as proof of pre-registration; the git hash is the
  machine-verifiable companion. Both are needed.
- If you prefer a lighter-weight timestamp than OSF, an alternative is to `git tag` + push and
  additionally post the artifact hash somewhere timestamped (e.g. an OSF file, or a tweet/permalink).
  OSF is the standard reviewers expect.
