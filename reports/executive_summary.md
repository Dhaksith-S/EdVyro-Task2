# Executive summary

## Decision and scope

For the fictional subscription retention team: identify customer groups worth investigating for avoidable churn, using the supplied synthetic customer snapshot. This is Task 02: Data Quality and Exploratory Analysis.

## Data overview

15 customers, 11 fields. 7 churned and 8 did not. The source is the EdVyro-supplied CSV, not a third-party replacement. No missing cells, exact duplicates, conflicting IDs, domain violations or IQR outliers were found under documented rules. All records were retained; no imputation or target modification was needed.

## Measured findings

- **Sample churn:** 7/15 customers (46.7%). The denominator is all supplied customers, not a monthly population.
- **Contract:** Month-to-Month has 7/7 churned (100.0%); the other contracts combined have 0/8 churned (0.0%). This perfect separation is a synthetic-sample limitation.
- **Tenure:** Mean tenure is 7.00 months for churned customers versus 29.12 for retained customers.
- **Support:** Churned customers average 4.29 tickets versus 1.00 for retained customers. The 3-or-more ticket band overlaps exactly with the churned group in this sample.
- **Spending and tier:** Mean monthly charges are 58.56 versus 107.49 for churned and retained customers respectively. Basic has 5/7 churned (71.4%). Tier, price, tenure, and contract overlap; none has an isolated estimated effect.

Payment-method churn rates and group denominators are available in [aggregate category results](category_summary.csv). These groups are small and overlap with contract and tier.

## Recommended next action

For the fictional subscription retention team, prioritize a review of early-tenure, Month-to-Month accounts with repeated support contacts. The observed 100% churn in the monthly-contract sample and the support-group difference support a hypothesis for investigation, not an intervention effect. In a larger authorized dataset, record observation dates, contact eligibility, ticket reasons and resolution times, and collect prospective outcomes. Measure next-period churn and ticket resolution in eligible contacted and comparison groups, using a randomized pilot where practical. Do not target people on gender or claim changing contract or price will prevent churn. The data owner should reconcile the generic guide with the actual schema and confirm currency, ticket window, billing definitions, missing-value policy and sharing rights.

## Analytical limitations

Only 15 synthetic records are supplied, with no sampling design, observation dates, churn window, or independent validation cohort. Rates describe this sample only. Perfect separation by contract and support-ticket band makes independent effects unidentifiable. Do not infer causes, deploy a prediction model, or estimate saved revenue. Individual service flags are absent; SubscriptionType is a tier, not a service inventory. The generic source guide has different field names and contract categories. INR and the 90-day ticket window are tentative guide mappings rather than CSV metadata. Billing history is unavailable, so TotalCharges = MonthlyCharges x TenureMonths is a descriptive sample consistency check, not a universal business rule.

No monthly churn trend or causal claim is supported. Currency totals are fictional and are not savings estimates. Public code, aggregate reports and charts can be reviewed now. Raw and cleaned customer-level CSVs remain local, and cleaned-CSV submission is pending permission or an authorized private delivery route.
