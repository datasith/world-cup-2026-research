# Freeze checklist — public prospective timestamp (after MD1, 2026-06-17)

Step-by-step to lock the live prediction. The **scientific value is the timestamp**: the model,
predictions, and scoring rule must be made public *before* MD2/MD3 are played. We use a **dated arXiv
note + a signed git tag + a Zenodo DOI** (not OSF, which is little used in this field); the SHA-256
digests give content integrity regardless of venue. The arXiv and Zenodo steps are manual (your
accounts); everything else is prepared.

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

Tag + push **before** posting, so arXiv/Zenodo can point at an existing public commit.

## 3. Establish the public timestamp

### 3a. Zenodo DOI (PRIMARY — immutable archived snapshot + citable DOI, no endorsement needed)
1. One-time: sign in at <https://zenodo.org> with GitHub/ORCID → **Settings → GitHub** → toggle the
   repo `datasith/world-cup-2026-research` **ON** (installs the release webhook). [done]
2. Ensure `.zenodo.json` (name, ORCID, license CC-BY-4.0) is committed and pushed. [done]
3. Cut a GitHub release at the current HEAD (which carries `.zenodo.json` and the frozen artifacts):
   `gh release create v1.0-freeze --title "Freeze: pre-registered MD3 predictions" --notes "Frozen MD3 manipulability predictions; see PREREGISTRATION.md and RESULTS.md R11. Freeze tag freeze-2026-06-18, commit ea30863."`
   Zenodo auto-archives the release and mints a **version DOI** (plus a concept DOI). The DOI's
   snapshot contains the byte-identical frozen artifacts; integrity is anchored by tag
   `freeze-2026-06-18` + the SHA-256 digests.
   - Requires the repo to be **public**. If private, use Zenodo **New upload** instead and attach
     `results/r4_freeze_elo.json`, `results/r4_freeze_poisson.json`, `PREREGISTRATION.md` → publish.

### 3b. arXiv companion note (SECONDARY/OPTIONAL — for reach)
1. Build `paper/arxiv_predictions.tex` → PDF; confirm it names the robust-set matches, the scoring
   rule, the freeze commit, and the two SHA-256 digests.
2. Submit at <https://arxiv.org/submit> — primary **stat.AP**, cross-list **cs.GT**, **physics.soc-ph**.
   Register with the `@caltech.edu` email for auto-endorsement; if endorsement is required and
   inconvenient, skip — the Zenodo DOI already provides the timestamp.

## 4. Record the identifiers back in the repo

Edit the `PREREGISTRATION.md` §0 header (and the manuscript's Prospective-predictions paragraph):
```
**Freeze commit:** ea3086323... (tag freeze-2026-06-18) · **arXiv:** 2506.XXXXX · **Zenodo DOI:** 10.5281/zenodo.XXXXXXX
```
```bash
git add PREREGISTRATION.md paper/main.tex && git commit -m "Record arXiv id + Zenodo DOI + freeze hash" && git push
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
- The **Zenodo DOI** is the primary public timestamp: a third-party, citable, immutable snapshot with
  a registration date that cannot be backdated, and it needs no endorsement. The **signed git tag +
  SHA-256 digests** are the machine-verifiable companions. An **arXiv note is secondary** (reach + an
  extra independent datestamp) but can require endorsement, so it is not on the critical path. We
  deliberately do not use OSF (low adoption in this field); integrity does not depend on the venue.
- Note for submission: under single-blind review (Nature default) author identity is visible anyway,
  so a public arXiv note is not a conflict; if opting into double-blind, anonymize the manuscript and
  be aware the public note makes true anonymity imperfect (still permitted).
