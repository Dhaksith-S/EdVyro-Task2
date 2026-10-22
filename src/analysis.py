"""Generate aggregate-only reports and figures from authorized local data."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, MaxNLocator
import numpy as np
import pandas as pd
import seaborn as sns

from src.data_cleaning import ROOT, DEFAULT_RAW, load_data, run
from src.data_validation import (NUMERIC, CATEGORIES, profile_columns, iqr_audit,
                                 validation_checks, quality_summary)

FIGURES = ['churn_overview.png', 'churn_by_contract.png', 'churn_by_payment.png',
           'churn_by_subscription.png', 'tenure_by_churn.png', 'spending_distributions.png',
           'numeric_correlations.png', 'support_by_churn.png']
LIMITATIONS = (
    'Only 15 synthetic records are supplied, with no sampling design, observation dates, '
    'churn window, or independent validation cohort. Rates describe this sample only. '
    'Perfect separation by contract and support-ticket band makes independent effects '
    'unidentifiable. Do not infer causes, deploy a prediction model, or estimate saved revenue. '
    'Individual service flags are absent; SubscriptionType is a tier, not a service inventory. '
    'The generic source guide has different field names and contract categories. INR and '
    'the 90-day ticket window are tentative guide mappings rather than CSV metadata. '
    'Billing history is unavailable, so TotalCharges = MonthlyCharges x TenureMonths is '
    'a descriptive sample consistency check, not a universal business rule.'
)


def segment_table(df: pd.DataFrame, column: str) -> pd.DataFrame:
    result = df.assign(churned=df.Churn.eq('Yes').astype(int)).groupby(column, observed=True).agg(
        customers=('churned', 'size'), churned=('churned', 'sum'))
    result['churn_pct'] = 100 * result.churned / result.customers
    return result.reset_index()


def summary_metrics(df: pd.DataFrame) -> dict:
    churned = df.Churn.eq('Yes')
    return {'customers': len(df), 'churned': int(churned.sum()),
            'churn_pct': float(churned.mean() * 100),
            'retained': int((~churned).sum()),
            'mean_tenure_churned': float(df.loc[churned, 'TenureMonths'].mean()),
            'mean_tenure_retained': float(df.loc[~churned, 'TenureMonths'].mean()),
            'mean_monthly_churned': float(df.loc[churned, 'MonthlyCharges'].mean()),
            'mean_monthly_retained': float(df.loc[~churned, 'MonthlyCharges'].mean()),
            'mean_tickets_churned': float(df.loc[churned, 'SupportTickets'].mean()),
            'mean_tickets_retained': float(df.loc[~churned, 'SupportTickets'].mean())}


def findings(df: pd.DataFrame) -> str:
    m = summary_metrics(df)
    contract = segment_table(df, 'ContractType').set_index('ContractType')
    monthly = contract.loc['Month-to-Month']
    other = df.loc[df.ContractType.ne('Month-to-Month')]
    basic = segment_table(df, 'SubscriptionType').set_index('SubscriptionType').loc['Basic']
    return (
        f"- **Sample churn:** {m['churned']}/{m['customers']} customers ({m['churn_pct']:.1f}%). The denominator is all supplied customers, not a monthly population.\n"
        f"- **Contract:** Month-to-Month has {int(monthly.churned)}/{int(monthly.customers)} churned ({monthly.churn_pct:.1f}%); the other contracts combined have {int(other.Churn.eq('Yes').sum())}/{len(other)} churned ({other.Churn.eq('Yes').mean()*100:.1f}%). This perfect separation is a synthetic-sample limitation.\n"
        f"- **Tenure:** Mean tenure is {m['mean_tenure_churned']:.2f} months for churned customers versus {m['mean_tenure_retained']:.2f} for retained customers.\n"
        f"- **Support:** Churned customers average {m['mean_tickets_churned']:.2f} tickets versus {m['mean_tickets_retained']:.2f} for retained customers. The 3-or-more ticket band overlaps exactly with the churned group in this sample.\n"
        f"- **Spending and tier:** Mean monthly charges are {m['mean_monthly_churned']:.2f} versus {m['mean_monthly_retained']:.2f} for churned and retained customers respectively. Basic has {int(basic.churned)}/{int(basic.customers)} churned ({basic.churn_pct:.1f}%). Tier, price, tenure, and contract overlap; none has an isolated estimated effect."
    )


def recommendations() -> str:
    return (
        'For the fictional subscription retention team, prioritize a review of early-tenure, '
        'Month-to-Month accounts with repeated support contacts. The observed 100% churn '
        'in the monthly-contract sample and the support-group difference support a hypothesis '
        'for investigation, not an intervention effect. In a larger authorized dataset, record '
        'observation dates, contact eligibility, ticket reasons and resolution times, and collect '
        'prospective outcomes. Measure next-period churn and ticket resolution in eligible '
        'contacted and comparison groups, using a randomized pilot where practical. Do not '
        'target people on gender or claim changing contract or price will prevent churn. '
        'The data owner should reconcile the generic guide with the actual schema and confirm '
        'currency, ticket window, billing definitions, missing-value policy and sharing rights.'
    )


def create_figures(df: pd.DataFrame) -> None:
    sns.set_theme(style='whitegrid', context='notebook', font='DejaVu Sans',
                  rc={'axes.spines.top': False, 'axes.spines.right': False,
                      'axes.titleweight': 'bold', 'figure.facecolor': '#ffffff'})
    palette = {'No': '#176b87', 'Yes': '#bd4f29'}
    folder = ROOT / 'figures'
    folder.mkdir(exist_ok=True)

    def save(fig, name):
        for ax in fig.axes:
            if ax.get_ylabel() == 'Customer count':
                ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        fig.text(0.01, 0.005, 'EdVyro synthetic sample | n=15 | Descriptive associations only', fontsize=9, color='#53616b')
        fig.tight_layout(rect=(0, 0.035, 1, 1))
        fig.savefig(folder / name, dpi=200, facecolor='white')
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.7))
    counts = df.Churn.value_counts().reindex(['No', 'Yes'], fill_value=0)
    bars = ax.bar(['Retained', 'Churned'], counts, color=[palette['No'], palette['Yes']], width=.55)
    ax.bar_label(bars, labels=[f'{n} customers ({n/len(df):.1%})' for n in counts], padding=6)
    ax.set(title='7 of 15 supplied customers churned', ylabel='Customer count', ylim=(0, 10))
    save(fig, FIGURES[0])
    for col, title, filename in [
        ('ContractType', 'Churn by contract type', FIGURES[1]),
        ('PaymentMethod', 'Churn by payment method', FIGURES[2]),
        ('SubscriptionType', 'Churn by subscription tier', FIGURES[3])]:
        table = segment_table(df, col)
        fig, ax = plt.subplots(figsize=(9, 4.9))
        bars = ax.bar(table[col], table.churn_pct, color='#bd4f29', width=.6)
        ax.bar_label(bars, labels=[f'{int(r.churned)}/{int(r.customers)} ({r.churn_pct:.1f}%)'
                                  for r in table.itertuples()], padding=6, fontsize=10)
        ax.set(title=title, ylabel='Churned customers / customers in group', ylim=(0, 118))
        ax.yaxis.set_major_formatter(PercentFormatter(100))
        save(fig, filename)
    fig, ax = plt.subplots(figsize=(9, 5))
    for value in ['No', 'Yes']:
        ax.hist(df.loc[df.Churn.eq(value), 'TenureMonths'], bins=[0, 6, 12, 24, 36, 49],
                histtype='step', linewidth=2.5, color=palette[value], label=f'Churn: {value}')
    ax.set(title='Churned customers have shorter tenure in this sample', xlabel='Tenure (months)', ylabel='Customer count')
    ax.legend()
    save(fig, FIGURES[4])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    for ax, col, label in zip(axes, ['MonthlyCharges', 'TotalCharges'], ['Monthly charges', 'Cumulative charges']):
        ax.hist(df[col], bins=5, color='#176b87', edgecolor='white')
        ax.set(title=label, xlabel='Recorded amount (INR per guide mapping)', ylabel='Customer count')
    save(fig, FIGURES[5])
    fig, ax = plt.subplots(figsize=(9, 7))
    corr = df[NUMERIC].assign(ChurnIndicator=df.Churn.eq('Yes').astype(int)).corr()
    labels = ['Age', 'Tenure', 'Monthly\ncharges', 'Total\ncharges', 'Support\ntickets', 'Churn\n(Yes=1)']
    sns.heatmap(corr, vmin=-1, vmax=1, cmap='vlag', annot=True, fmt='.2f', square=True,
                xticklabels=labels, yticklabels=labels, ax=ax, cbar_kws={'label': 'Pearson correlation'})
    ax.set_title('Numeric associations in a small synthetic sample', pad=15)
    save(fig, FIGURES[6])
    fig, ax = plt.subplots(figsize=(9, 4.8))
    for value in ['No', 'Yes']:
        ax.hist(df.loc[df.Churn.eq(value), 'SupportTickets'], bins=[-.5, 2.5, 6.5],
                histtype='step', linewidth=2.5, color=palette[value], label=f'Churn: {value}')
    ax.set(xticks=[1, 4.5], xticklabels=['0-2 tickets', '3-6 tickets'],
           title='Support-ticket bands separate the supplied groups', ylabel='Customer count', xlabel='Support tickets (guide suggests previous 90 days)')
    ax.legend()
    save(fig, FIGURES[7])


def generate() -> dict:
    raw = load_data()
    clean, decisions = run()
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    before = profile_columns(raw)
    after = profile_columns(clean)
    outliers = iqr_audit(clean)
    checks = validation_checks(clean)
    comparison = pd.DataFrame({'before': quality_summary(raw), 'after': quality_summary(clean)})
    categories = pd.concat([segment_table(clean, c).rename(columns={c: 'category'}).assign(column=c)
                            for c in CATEGORIES], ignore_index=True)
    statistics = clean[NUMERIC].describe().T
    metrics = summary_metrics(clean)
    for name, table in [('schema_audit', before), ('schema_cleaned', after), ('outlier_audit', outliers),
                        ('validation_results', checks), ('quality_comparison', comparison.rename_axis('metric').reset_index()),
                        ('category_summary', categories), ('summary_statistics', statistics.rename_axis('column').reset_index()),
                        ('cleaning_decisions', decisions)]:
        table.to_csv(reports / f'{name}.csv', index=False, float_format='%.6f')
    (reports / 'metrics.json').write_text(json.dumps(metrics, indent=2) + '\n', encoding='utf-8')
    create_figures(clean)
    md = lambda table: table.to_markdown(index=False, floatfmt='.2f')
    quality = f'''# Customer churn data-quality report

EdVyro Data Analytics Internship - Task 02. Analysis date: 22 October 2026.

## Initial dataset and provenance

The supplied sample contains **{len(raw)} rows and {len(raw.columns)} columns**. It is the dataset linked by the official Data Quality and Exploratory Analysis brief. No newer matching file was found in the workspace or accessible Downloads tree. The official curriculum calls this milestone 2, while the downloadable brief is named `data-analytics-task-1`. This is a numbering difference, not a replacement dataset.

The supplied file's SHA-256 is `{hashlib.sha256(DEFAULT_RAW.read_bytes()).hexdigest()}`. An unauthenticated fetch returned HTTP 403, so byte identity with the live endpoint could not be verified. Preserve the downloaded file as the source of truth. See [provenance](../src/provenance.json) and [input instructions](../data/raw/README.md).

## Schema, definitions and types

{md(before)}

The source guide's snake_case names are mapped conceptually to the CSV's actual headers. Its contract examples (monthly, quarterly, annual) conflict with this file's Month-to-Month, One Year, Two Year. No remapping or invented quarterly records are used. Definitions not explicit in the CSV are identified as inferred or tentative.

## Missing values and formatting

All {raw.size} required cells are present: {int(raw.isna().sum().sum())} missing values, and {int(checks.loc[checks['check']=='Blank strings','violations'].iloc[0])} blank strings. The schema table gives per-column counts and percentages. Whitespace and known-label case checks found no records requiring normalization. No missing values are filled with zero, a mean, or an inferred churn label.

## Duplicates and domains

Exact duplicate excess: {int(raw.duplicated().sum())}. Duplicate customer-ID excess: {int(raw.CustomerID.duplicated().sum())}. Excess counts exclude the first occurrence. Conflicting identifiers would stop the pipeline. Numeric parsing, finiteness, non-negativity, integer counts, identifier format and observed category vocabulary are checked below. The vocabulary is a sample validation contract, not a claim about every legitimate future category.

## Outliers and logical review

Tukey fences use Q1/Q3 from pandas' linear quantiles, with values outside Q1 - 1.5 IQR or Q3 + 1.5 IQR flagged. No flagged value is removed automatically.

{md(outliers)}

There are {int(outliers.flagged_rows.sum())} IQR flags across the numeric columns. Negative lower fences are statistical thresholds, not permissible negative business values. Age 0-120 is a review interval rather than an authoritative eligibility rule. Tenure is checked against age in months. All supplied totals agree with current monthly amount times tenure within 0.01; this arithmetic agreement cannot verify historical billing accuracy.

## Cleaning decisions and assumptions

The input already meets these quality rules. Explicit type casting, known-label normalization and exact-duplicate handling are implemented and logged, with zero observed record changes or deletions on this input. The exported CSV is a validated analysis-ready serialization; improvement is reproducibility and assurance rather than repaired values.

{md(decisions)}

`rows_affected` counts rows per action, including dtype-only changes when applicable. Counts may overlap and should not be summed as unique changed customers. Detected unknown labels, missing required fields, conflicting IDs or invalid numbers stop processing. Review checks are surfaced without speculative correction.

## Before versus after

{comparison.to_markdown(floatfmt='.0f')}

All {len(clean)} customer records and all churn labels are retained. No outliers are winsorized and no values are imputed. Output is reopened and compared against the in-memory cleaned data.

## Executed validation checks

{md(checks)}

## Descriptive statistics

{statistics.to_markdown(floatfmt='.2f')}

{findings(clean)}

## Residual limitations and readiness

{LIMITATIONS}

The dataset is ready for **descriptive analysis of this supplied sample** under the stated assumptions. This does not establish population representativeness, predictive performance or business impact. The raw and cleaned CSVs remain local because redistribution permission is absent. The notebook publishes only aggregates and binned plots. The mandatory cleaned-CSV delivery remains pending an authorized delivery route.

## Source links

- [Official curriculum and deliverables](https://edvyro.in/internships/data-analytics)
- [Official task checklist and dataset link](https://edvyro.in/datasets/task-kits/data-analytics-task-1)
- [Analysis guide](https://edvyro.in/datasets/source-materials/task-source-library#analytics) (supplied PDF, analytics page 3)
- [EdVyro terms, sections 10-11](https://edvyro.in/legal/terms)
'''
    (reports / 'data_quality_report.md').write_text(quality, encoding='utf-8')
    executive = f'''# Executive summary

## Decision and scope

For the fictional subscription retention team: identify customer groups worth investigating for avoidable churn, using the supplied synthetic customer snapshot. This is Task 02: Data Quality and Exploratory Analysis.

## Data overview

{len(clean)} customers, {len(clean.columns)} fields. {metrics['churned']} churned and {metrics['retained']} did not. The source is the EdVyro-supplied CSV, not a third-party replacement. No missing cells, exact duplicates, conflicting IDs, domain violations or IQR outliers were found under documented rules. All records were retained; no imputation or target modification was needed.

## Measured findings

{findings(clean)}

Payment-method churn rates and group denominators are available in [aggregate category results](category_summary.csv). These groups are small and overlap with contract and tier.

## Recommended next action

{recommendations()}

## Analytical limitations

{LIMITATIONS}

No monthly churn trend or causal claim is supported. Currency totals are fictional and are not savings estimates. Public code, aggregate reports and charts can be reviewed now. Raw and cleaned customer-level CSVs remain local, and cleaned-CSV submission is pending permission or an authorized private delivery route.
'''
    (reports / 'executive_summary.md').write_text(executive, encoding='utf-8')
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == '__main__':
    generate()
