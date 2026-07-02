# EEG-CogAgent

A reproducible, agent-orchestrated resting-state EEG biomarker workflow for
dementia differential analysis (Alzheimer's disease, frontotemporal
dementia, healthy controls) on public BIDS data.

The language model's role is to **standardize, document, audit, and draft**
the analysis workflow — BIDS loading, MNE preprocessing, interpretable EEG
feature extraction, statistics, leakage-safe machine-learning validation,
connectivity analysis, artifact auditing, and report drafting. Numerical
results are produced by deterministic Python modules; the language model
never diagnoses or alters them.

Priority dataset: OpenNeuro `ds004504`, a CC0 BIDS EEG dataset with
Alzheimer's disease, frontotemporal dementia, and healthy controls.

## Quick Start

```powershell
cd EEG-CogAgent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

Download the dataset into `data/ds004504` (see `scripts/download_ds004504.ps1`),
then run the pipeline:

```powershell
eeg-cogagent plan configs\ds004504_minimal.yaml
eeg-cogagent run  configs\ds004504_minimal.yaml --subjects-limit 6
eeg-cogagent run  configs\ds004504_minimal.yaml
```

The first run with `--subjects-limit 6` is a smoke test. The full run
writes features, statistics, model metrics, figures, and a Markdown report
under `results/ds004504_minimal`.

Post-hoc quality-control and confound-sensitivity analyses:

```powershell
python scripts\qc_ds004504.py            --config configs\ds004504_minimal.yaml
python scripts\adjusted_analysis.py      --config configs\ds004504_minimal.yaml
python scripts\pairwise_analysis.py      --config configs\ds004504_minimal.yaml
python scripts\residualized_analysis.py  --config configs\ds004504_minimal.yaml
python scripts\connectivity_analysis.py  --config configs\ds004504_minimal.yaml --workers 6
python scripts\generate_framework_figure.py --config configs\ds004504_minimal.yaml
eeg-cogagent run configs\ds006036_cross_condition.yaml
python scripts\cross_condition_validation.py
```

Audit the run:

```powershell
eeg-cogagent audit configs\ds004504_minimal.yaml
```

The audit verifies artifact completeness, cohort and prediction consistency,
metric ranges, optional extensions, software versions, and SHA-256
provenance. It writes `agent_audit.json`, `agent_audit.md`, and
`artifact_manifest.json` inside the selected result directory.

`ds006036` contains photomark recordings from the same participants as
`ds004504`. It is used for subject-disjoint cross-condition testing, not as
an independent external cohort. The independent external archive is OSF
node `2v5md`; see `eeg_cogagent/external_osf.py`.

## Repository

Source: <https://github.com/zisu-ai/EEG-CogAgent>
