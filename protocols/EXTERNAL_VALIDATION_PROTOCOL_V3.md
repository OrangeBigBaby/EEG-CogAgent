# External Validation Protocol v3 — Duplicate-Signal Integrity Correction

Status: predeclared, frozen **after** Codex's numerical review of v2 and **after**
content-level audit of the canonical OSF archive revealed a previously unflagged
exact-signal duplicate cluster. This is the integrity correction; v1 and v2 stay
as complete audit history and are not overwritten.

## Scope and claim boundaries

- **Independent external evaluation / generalization check** of a discovery
  model on the OSF `2v5md` archive. Not a clinical diagnostic claim, not a
  clinical-validity claim, not a state-of-the-art claim.
- **Binary AD vs HC only.** FTD is internal/exploratory; never enters the
  external model training or the primary domain-shift baseline.
- `ds006036` is the same participants as `ds004504` and is **not** treated as
  an external cohort.
- **v1 and v2 OSF labels and metrics were already inspected.** v3 is therefore
  a *post-hoc, method-audited integrity correction*, not a blinded / prospective
  / confirmatory validation. This is recorded in the report and review
  request.
- The deduplication rule is fixed **before** fitting and depends only on:
  (a) exact-signal SHA-256 content of the 19 common channels in canonical
      fixed order, with a `osf-common19-float64-v1` schema-version tag;
  (b) a deterministic natural-order representative rule (lexicographically
      smallest `participant_id` within a cluster).
  No probability, prediction, label, or metric value is used to form a cluster
  or pick a representative.
- Whatever the v3 metrics (up or down), they are saved and reported in full.
  No model / feature / threshold is changed using OSF labels or metrics.

## Data and integrity findings

- **Discovery:** OpenNeuro `ds004504` (CC0, DOI
  `10.18112/openneuro.ds004504.v1.0.9`, BIDS v1.2.1), 88 subjects
  (36 AD / 23 FTD / 29 HC). Training uses **AD + HC only (65)**.
- **External:** OSF node `2v5md`, file `EEG_data.zip`, canonical SHA-256
  `f5b30df4fd0d18e3224dde0bd564e2a5cea61845ae5a9b8142ae722c5d99ba93`.
  Article CC BY 4.0 (DOI `10.1038/s41598-023-32664-8`) but dataset node license
  null → **dataset reuse license UNRESOLVED**.
- **v3 integrity finding (read-only audit, hard-gated):**
  - Eyes-closed: nominal = 92 records (80 AD + 12 HC), unique common-19
    signal fingerprints = **88**, exactly one duplicate cluster of size 5
    (`AD_Paciente40`, `AD_Paciente41`, `AD_Paciente42`, `AD_Paciente43`,
    `AD_Paciente44`). 76 AD-labelled + 12 HC-labelled are unique.
  - Eyes-open: nominal = 91 records (80 AD + 11 HC, one Healthy folder absent
    vs Eyes-closed), unique = **87**. The same AD_Paciente40-44 duplicate
    cluster reproduces, confirming it is not a parsing artefact and the
    Eyes_open audit is captured as provenance only.
  - Treating the 92 eyes-closed folder IDs as 92 independent observations
    would violate independence (the duplicate cluster's rows are bit-identical
    on the 19 common channels plus F1/F2).
- **Primary observation unit = the unique common-19 signal fingerprint**.
  Per-cluster representative = the smallest `participant_id`. Expected primary
  cohort = **88 unique recording units (76 AD-labelled + 12 HC-labelled)**.
  We do **not** claim these are 88 unique persons.
- **Nominal 92** is preserved in v3 only as a clearly labelled non-primary
  audit carry-over so the divergence is visible.

## Feature space (unchanged from v2)

- Bands (half-open): delta [1,4), theta [4,8), alpha [8,13), beta [13,30). No
  gamma (OSF source band-limited to 0.5–30 Hz).
- Relative-power denominator = sum of the four 1–30 Hz bands.
- 36 features = 4 global + 20 regional relpowers + 2 global ratios
  (theta/alpha, delta/alpha) + 10 regional ratios. Same function, band edges,
  half-open rule, Welch 0.5 Hz resolution across both datasets.

## Model and training (v3 ≡ v2)

- Predeclared primary model: **L2 Logistic Regression, `class_weight="balanced"`.
- C grid: {0.1, 1.0, 10.0}; scoring `balanced_accuracy`.
- Threshold rule: `argmax balanced_accuracy` over `np.linspace(0.01, 0.99, 99)`,
  lowest threshold wins ties (deterministic).
- Internal nested-CV is unbiased (per outer fold, C and threshold selected on
  outer-train only; frozen and applied to outer-test).
- Final external model is fit on **all** ds004504 AD/HC; C and threshold
  chosen by discovery-only cross-fitting.
- **v3 model invariance vs v2:** the v3 final C, threshold, imputer/scaler
  parameters, and 36 standardized coefficients must be byte-identical to v2
  (asserted via the SHA-256 of the model's standard-form artefact; any
  divergence aborts v3 before publish).
- Sensitivity analysis (predeclared): also report external metrics at the
  fixed threshold 0.5.

## Statistics

- **Primary metrics:** balanced accuracy, ROC AUC, sensitivity, specificity,
  confusion matrix, all computed on the **88 unique primary records**.
- **BA and AUC:** subject-level, class-stratified bootstrap 95% CI, 10,000
  resamples, seed 42. CIs are *conditional on the fitted discovery model*.
- **Sensitivity/specificity:** Wilson score 95% CI (binomial).
- **Domain shift (primary):** label-free, discovery AD+HC (65) vs external
  primary records (88). The reported effect-size column is **`cohens_d`**
  using the standard sample-weighted pooled SD:
  `(mean_b - mean_a) / sqrt(((n_a-1)s_a^2 + (n_b-1)s_b^2) / (n_a+n_b-2))`. The
  formula is recorded in the JSON.
- **OOF traceability:** both `discovery_nested_oof_predictions.csv` and
  `discovery_threshold_oof_predictions.csv` carry `participant_id` and
  string `true_label` plus the existing fields. A run-time assertion
  guarantees the 65 discovery AD/HC IDs appear exactly once each.
- **No connectivity / graph external validation** (8 s records do not support it).
- **Nominal-92 audit** (non-primary): retained for transparency and explicitly
  labelled "violates independence because exact duplicates are counted
  repeatedly." Not used as the primary result and not optimised.

## Hard gates (the run does not publish unless all pass)

Canonical archive SHA-256; condition `Eyes_closed`; cohort audit has no fail;
fingerprint audit canonical facts for the canonical archive (Eyes_closed:
nominal 92, unique 88, exactly one size-5 duplicate cluster, 0 label
conflicts within any cluster; same audit ran on Eyes_open as a provenance
supplement); discovery 88 complete, training strictly 36 AD + 29 HC;
predictions IDs exactly equal the primary-representative set (88 rows).
Unknown labels are never silently mapped. Outputs are written to a staging
directory and published safely (the previous successful `output_dir`, if any,
is renamed to a backup; on full success the backup is removed; on failure the
backup is restored). On any failure the run returns non-zero and writes
neither `CODEX_REVIEW_REQUEST.md` nor a finalised `artifact_manifest.json`.

## Reproducibility

`validation_provenance.json` records the exact command, UTC time, interpreter,
package versions, seed, SHA-256 of key code and input files
(including the v3 protocol and the v2 result manifest), `environment.txt`
(`pip freeze`), and `artifact_manifest.json` (relative path, bytes, SHA-256
for every published artifact; the manifest excludes itself). `test_report.txt`
self-records the precise interpreter, the two pytest commands, the focused-
and full-test counts, and the exit codes.