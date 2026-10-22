# Customer churn data-quality report

EdVyro Data Analytics Internship - Task 02. Analysis date: 22 October 2026.

## Initial dataset and provenance

The supplied sample contains **15 rows and 11 columns**. It is the dataset linked by the official Data Quality and Exploratory Analysis brief. No newer matching file was found in the workspace or accessible Downloads tree. The official curriculum calls this milestone 2, while the downloadable brief is named `data-analytics-task-1`. This is a numbering difference, not a replacement dataset.

The supplied file's SHA-256 is `1d5048cad41e8abbefd5fab04cc7dd6579234a292a8f59f85d7d072f37fabdce`. An unauthenticated fetch returned HTTP 403, so byte identity with the live endpoint could not be verified. Preserve the downloaded file as the source of truth. See [provenance](../src/provenance.json) and [input instructions](../data/raw/README.md).

## Schema, definitions and types

| column           | dtype   |   missing |   missing_pct |   unique_nonmissing | definition                                                                      |
|:-----------------|:--------|----------:|--------------:|--------------------:|:--------------------------------------------------------------------------------|
| CustomerID       | str     |         0 |          0.00 |                  15 | Synthetic record identifier; never a numeric measure.                           |
| Gender           | str     |         0 |          0.00 |                   2 | Recorded gender label; sample labels are not an exhaustive real-world taxonomy. |
| Age              | int64   |         0 |          0.00 |                  15 | Customer age in years (inferred from field name).                               |
| TenureMonths     | int64   |         0 |          0.00 |                  15 | Completed months since signup (guide mapping).                                  |
| SubscriptionType | str     |         0 |          0.00 |                   3 | Recorded subscription tier; individual subscribed services are unavailable.     |
| MonthlyCharges   | float64 |         0 |          0.00 |                   3 | Fictional monthly amount; INR per guide mapping, not verified by CSV metadata.  |
| TotalCharges     | float64 |         0 |          0.00 |                  15 | Recorded cumulative amount; historical billing semantics are not supplied.      |
| ContractType     | str     |         0 |          0.00 |                   3 | Actual CSV contract label; retain Month-to-Month / One Year / Two Year.         |
| SupportTickets   | int64   |         0 |          0.00 |                   7 | Support ticket count; previous 90 days per guide mapping, unverified in CSV.    |
| PaymentMethod    | str     |         0 |          0.00 |                   4 | Recorded payment method.                                                        |
| Churn            | str     |         0 |          0.00 |                   2 | Yes means customer left; observation dates/window are not supplied.             |

The source guide's snake_case names are mapped conceptually to the CSV's actual headers. Its contract examples (monthly, quarterly, annual) conflict with this file's Month-to-Month, One Year, Two Year. No remapping or invented quarterly records are used. Definitions not explicit in the CSV are identified as inferred or tentative.

## Missing values and formatting

All 165 required cells are present: 0 missing values, and 0 blank strings. The schema table gives per-column counts and percentages. Whitespace and known-label case checks found no records requiring normalization. No missing values are filled with zero, a mean, or an inferred churn label.

## Duplicates and domains

Exact duplicate excess: 0. Duplicate customer-ID excess: 0. Excess counts exclude the first occurrence. Conflicting identifiers would stop the pipeline. Numeric parsing, finiteness, non-negativity, integer counts, identifier format and observed category vocabulary are checked below. The vocabulary is a sample validation contract, not a claim about every legitimate future category.

## Outliers and logical review

Tukey fences use Q1/Q3 from pandas' linear quantiles, with values outside Q1 - 1.5 IQR or Q3 + 1.5 IQR flagged. No flagged value is removed automatically.

| column         |     q1 |      q3 |   lower_fence |   upper_fence |   flagged_rows |
|:---------------|-------:|--------:|--------------:|--------------:|---------------:|
| Age            |  30.00 |   47.00 |          4.50 |         72.50 |              0 |
| TenureMonths   |   7.00 |   27.00 |        -23.00 |         57.00 |              0 |
| MonthlyCharges |  49.99 |  114.99 |        -47.51 |        212.49 |              0 |
| TotalCharges   | 449.91 | 3209.73 |      -3689.82 |       7349.46 |              0 |
| SupportTickets |   1.00 |    4.00 |         -3.50 |          8.50 |              0 |

There are 0 IQR flags across the numeric columns. Negative lower fences are statistical thresholds, not permissible negative business values. Age 0-120 is a review interval rather than an authoritative eligibility rule. Tenure is checked against age in months. All supplied totals agree with current monthly amount times tenure within 0.01; this arithmetic agreement cannot verify historical billing accuracy.

## Cleaning decisions and assumptions

The input already meets these quality rules. Explicit type casting, known-label normalization and exact-duplicate handling are implemented and logged, with zero observed record changes or deletions on this input. The exported CSV is a validated analysis-ready serialization; improvement is reproducibility and assurance rather than repaired values.

| issue                              | detection_method                                          | action                                                                   | justification                                                              |   rows_affected | validation_result   |
|:-----------------------------------|:----------------------------------------------------------|:-------------------------------------------------------------------------|:---------------------------------------------------------------------------|----------------:|:--------------------|
| CustomerID: formatting             | Compare trimmed identifier                                | Trim identifier whitespace; blank to missing                             | Preserve identifier case and do not guess unknown categories.              |               0 | PASS                |
| Gender: formatting                 | Trim and case-insensitive comparison with supplied labels | Trim surrounding whitespace; canonicalize known labels; blank to missing | Preserve identifier case and do not guess unknown categories.              |               0 | PASS                |
| SubscriptionType: formatting       | Trim and case-insensitive comparison with supplied labels | Trim surrounding whitespace; canonicalize known labels; blank to missing | Preserve identifier case and do not guess unknown categories.              |               0 | PASS                |
| ContractType: formatting           | Trim and case-insensitive comparison with supplied labels | Trim surrounding whitespace; canonicalize known labels; blank to missing | Preserve identifier case and do not guess unknown categories.              |               0 | PASS                |
| PaymentMethod: formatting          | Trim and case-insensitive comparison with supplied labels | Trim surrounding whitespace; canonicalize known labels; blank to missing | Preserve identifier case and do not guess unknown categories.              |               0 | PASS                |
| Churn: formatting                  | Trim and case-insensitive comparison with supplied labels | Trim surrounding whitespace; canonicalize known labels; blank to missing | Preserve identifier case and do not guess unknown categories.              |               0 | PASS                |
| Age: numeric type                  | Parse numbers and check integer fields                    | Use explicit numeric dtype                                               | Invalid numeric text fails instead of becoming an imputed value.           |               0 | PASS                |
| TenureMonths: numeric type         | Parse numbers and check integer fields                    | Use explicit numeric dtype                                               | Invalid numeric text fails instead of becoming an imputed value.           |               0 | PASS                |
| MonthlyCharges: numeric type       | Parse numbers and check integer fields                    | Use explicit numeric dtype                                               | Invalid numeric text fails instead of becoming an imputed value.           |               0 | PASS                |
| TotalCharges: numeric type         | Parse numbers and check integer fields                    | Use explicit numeric dtype                                               | Invalid numeric text fails instead of becoming an imputed value.           |               0 | PASS                |
| SupportTickets: numeric type       | Parse numbers and check integer fields                    | Use explicit numeric dtype                                               | Invalid numeric text fails instead of becoming an imputed value.           |               0 | PASS                |
| Exact duplicate records            | All-column equality after canonicalization                | Keep first exact record                                                  | Only exact copies are removable; conflicting customer IDs fail validation. |               0 | PASS                |
| Missing or invalid required values | Required-field and domain checks                          | No imputation; fail if unresolved                                        | No defensible replacement is supplied; never infer a missing target.       |               0 | PASS                |
| IQR extremes and billing review    | 1.5 x IQR; age/tenure and billing consistency diagnostics | Retain records; flag review checks without rewriting values              | Statistical extremes and billing deviations alone do not prove errors.     |               0 | PASS                |

`rows_affected` counts rows per action, including dtype-only changes when applicable. Counts may overlap and should not be summed as unique changed customers. Detected unknown labels, missing required fields, conflicting IDs or invalid numbers stop processing. Review checks are surfaced without speculative correction.

## Before versus after

|                             |   before |   after |
|:----------------------------|---------:|--------:|
| rows                        |       15 |      15 |
| columns                     |       11 |      11 |
| missing_cells               |        0 |       0 |
| exact_duplicates_excess     |        0 |       0 |
| duplicate_IDs_excess        |        0 |       0 |
| validation_error_violations |        0 |       0 |
| IQR_flags_across_columns    |        0 |       0 |

All 15 customer records and all churn labels are retained. No outliers are winsorized and no values are imputed. Output is reopened and compared against the in-memory cleaned data.

## Executed validation checks

| check                                                      |   violations | severity   | status   |
|:-----------------------------------------------------------|-------------:|:-----------|:---------|
| Nonempty dataset                                           |            0 | error      | PASS     |
| Missing required cells                                     |            0 | error      | PASS     |
| Blank strings                                              |            0 | error      | PASS     |
| Exact duplicate rows (excess)                              |            0 | error      | PASS     |
| Duplicate customer IDs (excess)                            |            0 | error      | PASS     |
| Identifier format                                          |            0 | error      | PASS     |
| Unparseable numeric cells                                  |            0 | error      | PASS     |
| Nonfinite numeric cells                                    |            0 | error      | PASS     |
| Negative numeric cells                                     |            0 | error      | PASS     |
| Noninteger count/age cells                                 |            0 | error      | PASS     |
| Age outside review interval 0-120                          |            0 | review     | PASS     |
| Tenure exceeds age in months                               |            0 | review     | PASS     |
| Gender: outside supplied sample vocabulary                 |            0 | error      | PASS     |
| SubscriptionType: outside supplied sample vocabulary       |            0 | error      | PASS     |
| ContractType: outside supplied sample vocabulary           |            0 | error      | PASS     |
| PaymentMethod: outside supplied sample vocabulary          |            0 | error      | PASS     |
| Churn: outside supplied sample vocabulary                  |            0 | error      | PASS     |
| Both churn classes present                                 |            0 | review     | PASS     |
| Total differs from current monthly amount x tenure (>0.01) |            0 | review     | PASS     |

## Descriptive statistics

|                |   count |    mean |     std |   min |    25% |     50% |     75% |     max |
|:---------------|--------:|--------:|--------:|------:|-------:|--------:|--------:|--------:|
| Age            |   15.00 |   39.07 |   11.39 | 23.00 |  30.00 |   38.00 |   47.00 |   60.00 |
| TenureMonths   |   15.00 |   18.80 |   14.33 |  2.00 |   7.00 |   15.00 |   27.00 |   48.00 |
| MonthlyCharges |   15.00 |   84.66 |   42.74 | 49.99 |  49.99 |   79.99 |  114.99 |  149.99 |
| TotalCharges   |   15.00 | 2088.48 | 2407.37 | 99.98 | 449.91 | 1099.78 | 3209.73 | 7199.52 |
| SupportTickets |   15.00 |    2.53 |    1.92 |  0.00 |   1.00 |    2.00 |    4.00 |    6.00 |

- **Sample churn:** 7/15 customers (46.7%). The denominator is all supplied customers, not a monthly population.
- **Contract:** Month-to-Month has 7/7 churned (100.0%); the other contracts combined have 0/8 churned (0.0%). This perfect separation is a synthetic-sample limitation.
- **Tenure:** Mean tenure is 7.00 months for churned customers versus 29.12 for retained customers.
- **Support:** Churned customers average 4.29 tickets versus 1.00 for retained customers. The 3-or-more ticket band overlaps exactly with the churned group in this sample.
- **Spending and tier:** Mean monthly charges are 58.56 versus 107.49 for churned and retained customers respectively. Basic has 5/7 churned (71.4%). Tier, price, tenure, and contract overlap; none has an isolated estimated effect.

## Residual limitations and readiness

Only 15 synthetic records are supplied, with no sampling design, observation dates, churn window, or independent validation cohort. Rates describe this sample only. Perfect separation by contract and support-ticket band makes independent effects unidentifiable. Do not infer causes, deploy a prediction model, or estimate saved revenue. Individual service flags are absent; SubscriptionType is a tier, not a service inventory. The generic source guide has different field names and contract categories. INR and the 90-day ticket window are tentative guide mappings rather than CSV metadata. Billing history is unavailable, so TotalCharges = MonthlyCharges x TenureMonths is a descriptive sample consistency check, not a universal business rule.

The dataset is ready for **descriptive analysis of this supplied sample** under the stated assumptions. This does not establish population representativeness, predictive performance or business impact. The raw and cleaned CSVs remain local because redistribution permission is absent. The notebook publishes only aggregates and binned plots. The mandatory cleaned-CSV delivery remains pending an authorized delivery route.

## Source links

- [Official curriculum and deliverables](https://edvyro.in/internships/data-analytics)
- [Official task checklist and dataset link](https://edvyro.in/datasets/task-kits/data-analytics-task-1)
- [Analysis guide](https://edvyro.in/datasets/source-materials/task-source-library#analytics) (supplied PDF, analytics page 3)
- [EdVyro terms, sections 10-11](https://edvyro.in/legal/terms)
