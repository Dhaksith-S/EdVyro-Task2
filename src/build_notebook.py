"""Build and execute the review notebook. Outputs deliberately contain aggregates only."""
import asyncio
import sys

import nbformat as nbf
from nbconvert.preprocessors import ExecutePreprocessor

from src.data_cleaning import ROOT


def build():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    cells = []

    def md(text):
        cells.append(nbf.v4.new_markdown_cell(text))

    def code(text):
        cells.append(nbf.v4.new_code_cell(text))

    md('''# Customer churn: data quality and exploratory analysis
## 1. Executive introduction
EdVyro Data Analytics Internship - Task 02. This notebook audits the supplied synthetic customer snapshot, produces a validated local CSV, and examines descriptive churn associations. All published outputs are aggregate tables or binned visualizations. No customer-level records are displayed.

**Data access:** provide the authorized input as described in `data/raw/README.md`. Raw and cleaned CSVs are excluded from Git. Cleaned-CSV delivery remains pending permission or an approved private route.''')
    md('''## 2. Business problem
Which customer groups should a fictional subscription retention team investigate first? Report evidence and uncertainty without claiming that contract, price, or support contacts cause churn. The denominator is the supplied customer snapshot; the observation window is unknown.''')
    code('''from pathlib import Path
import sys
ROOT = Path.cwd().resolve()
if not (ROOT / "src").is_dir():
    ROOT = ROOT.parent
assert (ROOT / "src").is_dir(), "Run from repository root or notebooks directory"
sys.path.insert(0, str(ROOT))
import json
import pandas as pd
pd.set_option("display.max_colwidth", None)
pd.set_option("display.max_columns", None)
from IPython.display import display, Markdown, Image
from src.data_cleaning import load_data, clean_data
from src.data_validation import profile_columns, validation_checks, iqr_audit, quality_summary, NUMERIC
from src.analysis import generate, segment_table, findings, recommendations, LIMITATIONS, FIGURES
raw = load_data()
print("Input loaded; aggregate-only output policy active.")''')
    md('''## 3. Dataset overview
The official curriculum calls this milestone 2, while its task kit is named `data-analytics-task-1`. The supplied brief links this customer churn CSV. No newer matching source was found in the workspace or accessible Downloads tree. The live endpoint returned HTTP 403, so remote byte identity could not be established. The exact local input checksum and source URLs are recorded below.''')
    code('''provenance = json.loads((ROOT / "src/provenance.json").read_text())
display(pd.Series({"rows": len(raw), "columns": len(raw.columns),
                   "source_sha256": provenance["source_sha256"],
                   "official_task": provenance["official_task_url"]}).to_frame("value"))''')
    md('''## 4. Data dictionary
Definitions follow actual CSV field names. INR and the prior-90-day support-ticket window come from a tentative generic-guide mapping. The guide's monthly/quarterly/annual contracts conflict with the supplied CSV; actual CSV labels are retained.''')
    code('display(profile_columns(raw)[["column", "definition"]])')
    md('''## 5. Initial data inspection
Inspect schema and aggregate dimensions without exposing a `head()` preview, customer IDs, or individual records.''')
    code('display(profile_columns(raw)[["column", "dtype", "unique_nonmissing"]])')
    md('''## 6. Data-quality profiling
Review required fields, domain membership, impossible numeric values and logical consistency. Unknown categories are rejected under this sample contract; they may be legitimate in future data and require owner review. Age bounds and current-rate billing equality are review diagnostics, not authoritative business restrictions.''')
    code('display(validation_checks(raw))')
    md('''## 7. Missing-value analysis
Count missing values per column and report their share of all rows. Also check whitespace-only strings. No unknown value is automatically converted into zero.''')
    code('display(profile_columns(raw)[["column", "missing", "missing_pct"]])')
    md('''## 8. Duplicate detection
An excess count excludes the first occurrence. Only fully identical records can be removed automatically; different records sharing an identifier must be resolved by the data owner.''')
    code('''display(pd.Series({"exact duplicate excess": int(raw.duplicated().sum()),
                   "duplicate ID excess": int(raw.CustomerID.duplicated().sum())}).to_frame("count"))''')
    md('''## 9. Outlier analysis
Use 1.5 times IQR fences with pandas linear quantiles on numeric fields. Flags prompt review; no extreme is automatically deleted or capped. Statistical fences do not define valid business ranges.''')
    code('display(iqr_audit(raw))')
    md('''## 10. Cleaning decisions
The source already meets the implemented quality rules. Preserve valid behavior and churn labels. The log records detection, action, justification, rows affected and validation result. A zero count means that operation was evaluated but changed no rows. Counts across actions need not represent distinct customers.''')
    code('''clean, decisions = clean_data(raw)
display(decisions)''')
    md('''## 11. Cleaning execution
Run the reusable pipeline, reopen the CSV for integrity checks, and regenerate reports and figures. The raw file is never overwritten. The cleaned file is written locally to `data/processed/customer_churn_cleaned.csv` and stays excluded from the public commit.''')
    code('''metrics = generate()
reopened = load_data(ROOT / "data/processed/customer_churn_cleaned.csv")
pd.testing.assert_frame_equal(clean, reopened, check_dtype=False)
display(pd.DataFrame({"before": quality_summary(raw), "after": quality_summary(clean)}))''')
    md('''## 12. Validation results
All required fields must pass. Target review checks require both classes for this exploration, without imposing an invented acceptable population churn rate. Review issues remain visible for human interpretation.''')
    code('''checks = validation_checks(clean)
assert checks.status.eq("PASS").all(), "Investigate validation or review issues"
assert raw.equals(clean), "Supplied snapshot should be preserved without value changes"
display(checks)''')
    md('''## 13. Descriptive statistics
Customer identifiers are excluded from measures. Numeric statistics and category counts summarize this small synthetic snapshot only.''')
    code('''display(clean[NUMERIC].describe().T.round(2))
for col in ["Churn", "ContractType", "PaymentMethod", "SubscriptionType"]:
    display(segment_table(clean, col).round(2))''')
    md('''## 14. Exploratory data visualizations
PNG files are saved at 200 dpi. Categorical churn rates show group numerators and denominators. Histograms aggregate tenure, spending and support contacts; no row-level scatter or identifier plot is published. Pearson correlations describe associations and include the explicitly encoded target (Yes = 1).''')
    code('''for name in FIGURES:
    display(Image(filename=str(ROOT / "figures" / name), width=850))''')
    md('## 15. Key business insights')
    code('display(Markdown(findings(clean)))')
    md('## 16. Limitations')
    code('display(Markdown(LIMITATIONS))')
    md('## 17. Recommendations')
    code('display(Markdown(recommendations()))')
    md('''## 18. Conclusion
The supplied snapshot can support reproducible descriptive exploration under the documented assumptions. No artificial defects were introduced, and no valid records or targets were discarded. The separate automated tests exercise missing values, malformed categories/numbers, duplicates, preservation and reproducibility. See `reports/verification.md` for executed evidence and `reports/submission_checklist.md` for criterion status.

Public code, executed notebook, aggregate reports and figures are available for review. The mandatory cleaned CSV has been generated and validated locally, but its authorized delivery is still pending. A repository link alone does not complete that missing requirement.

Sources: [official curriculum](https://edvyro.in/internships/data-analytics), [task checklist](https://edvyro.in/datasets/task-kits/data-analytics-task-1), [analysis guide](https://edvyro.in/datasets/source-materials/task-source-library#analytics), [terms](https://edvyro.in/legal/terms).''')
    nb = nbf.v4.new_notebook(cells=cells, metadata={
        'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}})
    # Stable cell IDs make a rebuilt notebook easier to review.
    for index, cell in enumerate(nb.cells):
        cell['id'] = f'churn-{index:02d}'
    ExecutePreprocessor(timeout=180, kernel_name='python3').preprocess(nb, {'metadata': {'path': str(ROOT)}})
    for cell in nb.cells:
        cell.metadata.pop('execution', None)
        for output in cell.get('outputs', []):
            if output.output_type == 'error':
                raise RuntimeError('Notebook contains an error')
            if output.output_type == 'stream' and 'warning' in output.text.lower():
                raise RuntimeError('Notebook contains an unexplained warning')
    path = ROOT / 'notebooks/customer_churn_eda.ipynb'
    nbf.write(nb, path)
    print(f'Executed {sum(c.cell_type == "code" for c in cells)} code cells; no errors or warning outputs.')


if __name__ == '__main__':
    build()
