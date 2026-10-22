# Executed verification

Verified locally on 22 October 2026 with Windows and Python 3.11.9. Customer-level CSVs remain local and are excluded from Git.

| Check | Actual result |
| --- | --- |
| `python -m src.data_cleaning` | PASS: 15 rows exported, reopened and compared with cleaned in-memory data |
| `python -m src.analysis` | PASS: eight 200-dpi PNGs, aggregate tables and both narrative reports generated |
| `python -m src.build_notebook` | PASS: all 16 code cells executed; no error or warning outputs saved |
| `python -m nbconvert --to notebook --execute --inplace notebooks/customer_churn_eda.ipynb` | PASS: independent execution completed successfully |
| `python -m pytest -q` | PASS: **33 passed** |
| `python -m pip check` | PASS: no broken requirements |
| `python -m pip install -r requirements.txt` | PASS: pinned direct dependencies install in the tested environment |
| CSV integrity | PASS: source SHA-256 matches provenance; all 15 rows, 11 fields and original churn labels preserved |
| Quality checks | PASS: all 19 required and review diagnostics pass on this snapshot |
| Fault injection | PASS: malformed numeric text, negative/nonfinite values, missing values, blanks, unknown labels, conflicting IDs and fractional counts rejected; exact duplicates resolved; outlier retained and flagged |
| Publication content | Notebook contains no customer identifiers or row previews; plots use aggregates and bins |
| Visual review | All eight PNGs inspected for titles, axis labels, legends, count/rate labels and clipping |
| Relative links | Automated Markdown file and figure reference checks pass |
| Task 1 preservation | Original three files' SHA-256 checks retained for final comparison; no Task 1 edits made |
| Remote verification | Pending initial push; final results recorded after GitHub checks |

The kernel launcher printed an environment warning that local Jupyter TCP transport is not encrypted. The independent Windows nbconvert run also printed a Proactor/ZeroMQ compatibility warning and automatically used a selector thread; execution completed. The notebook builder explicitly uses the Windows selector event loop. These launcher diagnostics are not notebook cell warnings. Jupyter was used locally for execution, not exposed as a public server.

The tests exercise actual source data plus temporary in-memory fault copies. Missing input fails with an actionable message. The exact sample checksum is intentional: a different official input requires provenance and result review. The test environment's transitive dependencies are recorded in [requirements-lock.txt](../requirements-lock.txt).

No claim is made that the missing cleaned-CSV submission requirement is satisfied. See the [criterion checklist](submission_checklist.md).
