## 2025-04-03

`surveys/hf_survey/longitudinal/pickle_only_models_mar2025.txt`:
MARCH-PICKLE: List of repositories that contain only pickle models, and their
number of downloads, for March 2025.

`surveys/paper_survey_1664.csv`:
PREV-ANALYZED: Outdated CSV containing results of downloading 1664 repositories, tracing the
pickle models, and tracking the callables used.

To sample `n` models from the MARCH-PICKLE, but reuse analysis that we've
already done, I determined which new repositories are introduced in
MARCH-PICKLE that are not already in PREV-ANALYZED:
- use the `scripts/determine_additional_downloads.py` - the output
  `missing_models` file contains a list of repos that must be downloaded and
  traced.
- Use it as input to the `scripts/download_model.py` script to begin download:
  `python3 scripts/download_model.py --repositories-list missing_models --outdir <path>`
- Post-process results:
    `python3 analyze_traces.py <path to traces> > traced.csv`

- Combine results with previous analysis:
    Create list of all repositories to include:
        `cat missing existing > all`
    `python3 scripts/merge_trace_csv ...`
    `python3 process_csv.py <csv>`
