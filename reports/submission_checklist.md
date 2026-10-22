# Task 02 submission checklist

Status distinguishes executed local analysis from public delivery. A repository link is not EdVyro approval.

| Criterion | Status | Evidence |
| --- | --- | --- |
| Profile columns and data types | PASS | [Schema audit](schema_audit.csv) |
| Assess missing values and blank strings | PASS | [Quality report](data_quality_report.md) and [validation](validation_results.csv) |
| Assess exact duplicates and duplicate customer IDs | PASS | [Before/after](quality_comparison.csv) |
| Assess outliers and impossible values | PASS | [IQR audit](outlier_audit.csv) and [validation](validation_results.csv) |
| Document cleaning decisions and assumptions | PASS | [Cleaning log](cleaning_decisions.csv) |
| Execute validation checks | PASS | [Validation results](validation_results.csv) |
| Generate and reopen cleaned CSV locally | PASS | Local file is ignored by Git; [output instructions](../data/processed/README.md) |
| Calculate summary statistics | PASS | [Numeric statistics](summary_statistics.csv) |
| Inspect meaningful distributions and churn segments | PASS | [Figures](../figures/churn_by_contract.png) and [category summary](category_summary.csv) |
| Execute reproducible notebook | PASS | [Notebook](../notebooks/customer_churn_eda.ipynb) and [verification](verification.md) |
| Complete data-quality report | PASS | [Report](data_quality_report.md) |
| Publish permissible review files in a public repository | PASS | [Public repository](https://github.com/Dhaksith-S/EdVyro-Task2), anonymous file access and server-rendered README/notebook verified |
| Deliver mandatory cleaned CSV by an authorized method | **PENDING** | No redistribution permission or approved private delivery method supplied |
| Entire mandatory submission complete | **PENDING** | Cleaned-CSV delivery must be resolved before claiming full compliance |

Official checks: [curriculum](https://edvyro.in/internships/data-analytics), [task guide](https://edvyro.in/datasets/task-kits/data-analytics-task-1).
