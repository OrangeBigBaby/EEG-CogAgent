# -*- coding: utf-8 -*-
"""Content audit for the Frontiers in Neurology submission package.

Mirrors the spirit of tests/test_jnm_v3_1_content_audit.py but adapted to
Frontiers Original Research rules:

- abstract <=350 words
- main text <=12 000 words
- 5 <= keywords <= 8
- figures + tables <= 15
- all 22 in-text citations match the bibliography
- required evidence phrases are present (88 unique recordings, 0.873,
  0.967, UNRESOLVED, post-hoc, osf-common19-float64-v2, etc.)
- no forbidden phrases (state-of-the-art, clinical-grade, 92 independent
  subjects, 88 unique persons, prospective clinical validation, etc.)
- CRediT draft is honest (no Investigation / Resources / Clinical
  interpretation claims that the author has not confirmed)
- OSF dataset-node license kept as UNRESOLVED
- ds006036 not described as an external cohort

Writes qa/CONTENT_AUDIT.json. Exit code 0 only if every gate passes.
"""
from __future__ import annotations
import json, os, re, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "work", "frontiers_build"))
import content as C  # noqa: E402
import refs as R  # noqa: E402

OUT = os.path.join(REPO, "submission", "frontiers_neurology_v1",
                   "qa", "CONTENT_AUDIT.json")


def _word_count(s: str) -> int:
    return len(re.findall(r"\S+", s))


def _main_text_word_count() -> int:
    return sum(_word_count(t) for _, t in C.MAIN_TEXT)


def _abstract_word_count() -> int:
    return _word_count(C.ABSTRACT)


def _scope_word_count() -> int:
    return _word_count(C.SCOPE_STATEMENT)


def _contribution_word_count() -> int:
    return _word_count(C.CONTRIBUTION_TO_FIELD)


def _all_text() -> str:
    parts = [C.TITLE, C.RUNNING_TITLE, C.AUTHOR_LINE, C.CORRESPONDENCE,
             C.ABSTRACT]
    parts.extend([t for _, t in C.MAIN_TEXT])
    parts.extend([C.AUTHOR_CONTRIBUTIONS, C.FUNDING, C.CONFLICT_OF_INTEREST,
                  C.ACKNOWLEDGMENTS, C.DATA_AVAILABILITY, C.ETHICS, C.GEN_AI,
                  C.SUPPLEMENTARY])
    parts.extend([cap + body for cap, body in C.FIGURE_CAPTIONS])
    return "\n\n".join(parts)


def run() -> dict:
    body = _all_text()
    body_lc = body.lower()

    # -- forbidden phrases (case-insensitive) -------------------------------
    # Each entry is forbidden UNLESS it is negated in a small surrounding
    # window (the manuscript is allowed to say "we did NOT do X").
    FORBIDDEN = [
        "state-of-the-art",
        "clinical-grade",
        "prospectively validated",
        "diagnostic deployment",
        "autonomous diagnosis",
        "autonomous diagnostic",
        "92 independent subjects",
        "92 independent persons",
        "88 unique persons",
        "88 unique people",
        "92 unique persons",
        "92 unique people",
        "subject-level external bootstrap",
        "multimodal fusion",
        "diagnostic adjudication",  # we did not do it
        "manual-versus-agent comparison",  # we did not do it
    ]
    # Negation cues within ~200 chars either side.
    NEG = ("not ", "no ", "never ", "did not", "do not", "without ",
           "neither ", "nor ", "lack", "absence", "lacks", "lacking",
           "non-", "un-", "no new ", "no manual",
           "not positioned", "not claim", "not a", "does not",
           "is not a", "is not positioned", "future work",
           "should ", "future ", "would ", "could ",
           "did not perform", "we did not")

    forbidden_present = {}
    for f in FORBIDDEN:
        for m in re.finditer(re.escape(f), body_lc):
            window = body_lc[max(0, m.start() - 200):m.end() + 200]
            if any(cue in window for cue in NEG):
                continue
            forbidden_present[f] = True
            break

    # -- required phrases ---------------------------------------------------
    REQUIRED = [
        "0.873",          # external BA
        "0.967",          # external AUC
        "0.772",          # external BA CI low
        "0.917",          # external AUC CI low
        "0.947",          # external BA CI high
        "1.000",          # external AUC CI high (rendered as 1.000)
        "88 unique recordings",
        "92 nominal records",
        "76",
        "12 controls",
        "osf-common19-float64-v2",
        "unresolved",
        "post-hoc",
        "alzheimer",
        "frontotemporal",
        "ds004504",
        "ds006036",
        "2v5md",
        "EEG-CogAgent",
    ]
    required_missing = []
    for r in REQUIRED:
        if r.lower() not in body_lc:
            required_missing.append(r)

    # -- abstract, main text, scope, contribution length --------------------
    absw = _abstract_word_count()
    mtw = _main_text_word_count()
    scope_w = _scope_word_count()
    contrib_w = _contribution_word_count()

    counts_block = {
        "abstract_words": absw,
        "abstract_le_350": absw <= 350,
        "main_text_words": mtw,
        "main_text_le_12000": mtw <= 12000,
        "keyword_count": len(C.KEYWORDS),
        "keyword_count_in_range": 5 <= len(C.KEYWORDS) <= 8,
        "figures_count": len(C.FIGURE_CAPTIONS),
        "tables_count": len(C.TABLES),
        "figs_plus_tables": len(C.FIGURE_CAPTIONS) + len(C.TABLES),
        "figs_plus_tables_le_15": (len(C.FIGURE_CAPTIONS) + len(C.TABLES)) <= 15,
        "references_count": len(R.REFERENCES),
        "scope_words": scope_w,
        "scope_le_200": scope_w <= 200,
        "contribution_words": contrib_w,
        "contribution_le_200": contrib_w <= 200,
    }

    # -- citation integrity ------------------------------------------------
    cited = set()
    for _, t in C.MAIN_TEXT:
        for m in re.finditer(r"(?<!\d)\[(\s*\d+\s*(?:,\s*\d+\s*)*)\](?!\d)", t):
            for n_str in re.findall(r"\d+", m.group(1)):
                cited.add(int(n_str))
    # End-matter sections also carry citations.
    for s in (C.AUTHOR_CONTRIBUTIONS, C.FUNDING, C.CONFLICT_OF_INTEREST,
              C.ACKNOWLEDGMENTS, C.DATA_AVAILABILITY, C.ETHICS, C.GEN_AI,
              C.SUPPLEMENTARY):
        for m in re.finditer(r"(?<!\d)\[(\s*\d+\s*(?:,\s*\d+\s*)*)\](?!\d)", s):
            for n_str in re.findall(r"\d+", m.group(1)):
                cited.add(int(n_str))
    bib_numbers = {n for n, _, _ in R.REFERENCES}
    citation_in_text_not_in_bib = sorted(cited - bib_numbers)
    citation_in_bib_not_in_text = sorted(bib_numbers - cited)

    # -- CRediT honesty check ----------------------------------------------
    # The drafted AUTHOR_CONTRIBUTIONS must not assert roles that were not
    # confirmed by the author.  The pattern "AUTHOR CONFIRMATION REQUIRED"
    # must be present so the draft does not silently claim unconfirmed roles.
    credit_str = C.AUTHOR_CONTRIBUTIONS
    credit_has_confirmation_marker = "AUTHOR CONFIRMATION REQUIRED" in credit_str

    # -- ds006036 must NOT be called an external cohort --------------------
    ds006036_ok = True
    NEG_DS = ("not ", "no ", "rather than", "never ", "did not", "do not",
              "paired", "same cohort", "same participants", "same site",
              "same device", "cross-condition", "within-cohort",
              "transfer within", "treated as a paired", "paired cross-condition",
              "shared")
    for m in re.finditer(r"ds006036", body):
        window = body[max(0, m.start() - 100):m.end() + 100].lower()
        if "external cohort" in window and not any(c in window for c in NEG_DS):
            ds006036_ok = False
            break
        if "external validation" in window and not any(c in window for c in NEG_DS):
            ds006036_ok = False
            break

    # -- OSF dataset license kept as UNRESOLVED -----------------------------
    # Mirrors the JNM v3.1 content-audit rule: "UNRESOLVED" and
    # "dataset node license" both appear in the manuscript body.
    osf_unresolved = (
        "unresolved" in body_lc
        and "dataset node license" in body_lc
    )

    # -- author emails / ORCIDs not invented -------------------------------
    # The five authors' emails must be exactly the five supplied in chat.
    expected_emails = {
        "zhaizisu@gmail.com",
        "smhdoctor@163.com",
        "gaodan1803@163.com",
        "sheelokeyuan@gmail.com",
        "caolei_163@163.com",
    }
    emails_in_text = set(re.findall(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", body))
    emails_unexpected = emails_in_text - expected_emails
    email_audit_ok = (len(emails_unexpected) == 0)

    # -- decision ----------------------------------------------------------
    failures = []
    if forbidden_present:
        failures.append(f"forbidden_phrases_present={list(forbidden_present)}")
    if required_missing:
        failures.append(f"required_phrases_missing={required_missing}")
    for k in ("abstract_le_350", "main_text_le_12000",
              "keyword_count_in_range", "figs_plus_tables_le_15",
              "scope_le_200", "contribution_le_200"):
        if not counts_block[k]:
            failures.append(f"count_gate_fail={k}")
    if citation_in_text_not_in_bib:
        failures.append(f"citations_missing_from_bib={citation_in_text_not_in_bib}")
    if citation_in_bib_not_in_text:
        failures.append(f"bibliography_entries_never_cited={citation_in_bib_not_in_text}")
    if not credit_has_confirmation_marker:
        failures.append("credit_draft_lacks_AUTHOR_CONFIRMATION_REQUIRED_marker")
    if not ds006036_ok:
        failures.append("ds006036_described_as_external_cohort")
    if not osf_unresolved:
        failures.append("osf_license_resolution_dropped")
    if not email_audit_ok:
        failures.append(f"unexpected_emails_present={sorted(emails_unexpected)}")

    status = "PASS" if not failures else "FAIL"

    audit = {
        "manuscript_source": "work/frontiers_build/content.py",
        "references_source": "work/frontiers_build/refs.py",
        "supplementary_source": "work/frontiers_build/supp_source.json",
        "title": C.TITLE,
        "article_type": C.ARTICLE_TYPE,
        "running_title": C.RUNNING_TITLE,
        "author_line": C.AUTHOR_LINE,
        "counts": counts_block,
        "forbidden_phrases_present": forbidden_present,
        "required_phrases_missing": required_missing,
        "citations": {
            "cited_in_text": sorted(cited),
            "in_bibliography": sorted(bib_numbers),
            "in_text_not_in_bib": citation_in_text_not_in_bib,
            "in_bib_not_in_text": citation_in_bib_not_in_text,
            "all_match": (not citation_in_text_not_in_bib
                          and not citation_in_bib_not_in_text),
        },
        "credit_draft_marker_present": credit_has_confirmation_marker,
        "ds006036_not_external_cohort": ds006036_ok,
        "osf_license_kept_unresolved": osf_unresolved,
        "emails_in_text": sorted(emails_in_text),
        "expected_author_emails": sorted(expected_emails),
        "unexpected_emails": sorted(emails_unexpected),
        "status": status,
        "failures": failures,
        "note": (
            "Generated by scripts/audit_frontiers_content.py from "
            "work/frontiers_build/content.py.  Numeric thresholds and "
            "phrase rules per prompts/claude_frontiers_neurology_submission_"
            "rebuild_v1.md section 14."
        ),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(audit, fh, indent=2, ensure_ascii=False)
    print(f"WROTE {OUT}")
    print(f"  status={status}")
    if failures:
        for f in failures:
            print(f"  - {f}")
    return audit


if __name__ == "__main__":
    audit = run()
    sys.exit(0 if audit["status"] == "PASS" else 1)
