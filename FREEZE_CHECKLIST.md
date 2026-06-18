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

## 3. Establish the public timestamp (arXiv + Zenodo)

### 3a. arXiv predictions note (the primary, backdate-proof timestamp)
1. Build `paper/arxiv_predictions.tex` → PDF (`pdflatex arxiv_predictions.tex`); confirm it names the
   robust-set matches, the scoring rule, the freeze commit, and the two SHA-256 digests.
2. Submit at <https://arxiv.org/submit> — category **stat.AP** (cross-list **physics.soc-ph** and/or
   **econ.GN**). Source upload (the `.tex`) is preferred over PDF-only.
3. arXiv moderation can take 1–2 business days; submit **now** so it posts before MD3 (~June 23–27).
   The arXiv submission datestamp is the unfakeable public timestamp.

### 3b. Zenodo DOI (immutable archived snapshot of the artifacts)
1. One-time: sign in at <https://zenodo.org> with GitHub/ORCID → **Settings → GitHub** → toggle the
   repo `datasith/world-cup-2026-research` **ON** (this installs the release webhook).
2. Edit `.zenodo.json` to fill your name + ORCID (currently placeholders), commit, push.
3. Cut a GitHub release **on the freeze tag**: `gh release create freeze-2026-06-18 --title "Freeze: pre-registered MD3 predictions" --notes "see PREREGISTRATION.md"` (or via the GitHub UI). Zenodo
   auto-archives that release and mints a **version DOI** (plus a concept DOI).
   - Requires the repo to be **public**. If it must stay private, instead use Zenodo **New upload**
     and attach `results/r4_freeze_elo.json`, `results/r4_freeze_poisson.json`, `PREREGISTRATION.md`
     manually → publish → DOI.

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
- The **arXiv datestamp** is the primary proof the predictions predate the outcomes (third-party,
  cannot be backdated); the **Zenodo DOI** gives a citable, immutable artifact snapshot; the **signed
  git tag + SHA-256 digests** are the machine-verifiable companions. We deliberately do not use OSF
  (low adoption in this field); the integrity guarantee does not depend on the venue.
- Note for submission: under single-blind review (Nature default) author identity is visible anyway,
  so a public arXiv note is not a conflict; if opting into double-blind, anonymize the manuscript and
  be aware the public note makes true anonymity imperfect (still permitted).
