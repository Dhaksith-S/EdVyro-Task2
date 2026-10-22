"""Schema and evidence-based checks. Flag uncertainty without inventing corrections."""
from __future__ import annotations

import numpy as np
import pandas as pd

COLUMNS = ['CustomerID', 'Gender', 'Age', 'TenureMonths', 'SubscriptionType',
           'MonthlyCharges', 'TotalCharges', 'ContractType', 'SupportTickets',
           'PaymentMethod', 'Churn']
INTEGERS = ['Age', 'TenureMonths', 'SupportTickets']
NUMERIC = ['Age', 'TenureMonths', 'MonthlyCharges', 'TotalCharges', 'SupportTickets']
CATEGORIES = {
    'Gender': ['Female', 'Male'],
    'SubscriptionType': ['Basic', 'Pro', 'Enterprise'],
    'ContractType': ['Month-to-Month', 'One Year', 'Two Year'],
    'PaymentMethod': ['Credit Card', 'Bank Transfer', 'UPI', 'Debit Card'],
    'Churn': ['Yes', 'No'],
}
DEFINITIONS = {
    'CustomerID': 'Synthetic record identifier; never a numeric measure.',
    'Gender': 'Recorded gender label; sample labels are not an exhaustive real-world taxonomy.',
    'Age': 'Customer age in years (inferred from field name).',
    'TenureMonths': 'Completed months since signup (guide mapping).',
    'SubscriptionType': 'Recorded subscription tier; individual subscribed services are unavailable.',
    'MonthlyCharges': 'Fictional monthly amount; INR per guide mapping, not verified by CSV metadata.',
    'TotalCharges': 'Recorded cumulative amount; historical billing semantics are not supplied.',
    'ContractType': 'Actual CSV contract label; retain Month-to-Month / One Year / Two Year.',
    'SupportTickets': 'Support ticket count; previous 90 days per guide mapping, unverified in CSV.',
    'PaymentMethod': 'Recorded payment method.',
    'Churn': 'Yes means customer left; observation dates/window are not supplied.',
}


def check_schema(df: pd.DataFrame) -> None:
    if list(df.columns) != COLUMNS:
        raise ValueError(f'Expected ordered columns {COLUMNS}; got {list(df.columns)}')


def numeric_view(df: pd.DataFrame) -> pd.DataFrame:
    return df[NUMERIC].apply(pd.to_numeric, errors='coerce')


def validation_checks(df: pd.DataFrame) -> pd.DataFrame:
    check_schema(df)
    number = numeric_view(df)
    rows = []

    def add(name, violations, severity='error'):
        rows.append({'check': name, 'violations': int(violations), 'severity': severity,
                     'status': 'PASS' if violations == 0 else ('REVIEW' if severity == 'review' else 'FAIL')})

    add('Nonempty dataset', int(df.empty))
    add('Missing required cells', df.isna().sum().sum())
    texts = df.select_dtypes(include=['object', 'string'])
    add('Blank strings', sum(texts[c].fillna('').str.strip().eq('').sum() for c in texts))
    add('Exact duplicate rows (excess)', df.duplicated().sum())
    add('Duplicate customer IDs (excess)', df.CustomerID.duplicated().sum())
    add('Identifier format', (~df.CustomerID.astype('string').str.fullmatch(r'CUST-\d+', na=False)).sum())
    add('Unparseable numeric cells', (number.isna() & df[NUMERIC].notna()).sum().sum())
    add('Nonfinite numeric cells', ((~np.isfinite(number)) & number.notna()).sum().sum())
    add('Negative numeric cells', (number < 0).sum().sum())
    add('Noninteger count/age cells', (number[INTEGERS].notna() & number[INTEGERS].mod(1).ne(0)).sum().sum())
    add('Age outside review interval 0-120', ((number.Age < 0) | (number.Age > 120)).sum(), 'review')
    add('Tenure exceeds age in months', (number.TenureMonths > number.Age * 12).sum(), 'review')
    for col, values in CATEGORIES.items():
        add(f'{col}: outside supplied sample vocabulary', (~df[col].isin(values) & df[col].notna()).sum())
    add('Both churn classes present', int(set(df.Churn.dropna()) != {'Yes', 'No'}), 'review')
    # This equality describes the supplied sample, not a universal billing rule.
    add('Total differs from current monthly amount x tenure (>0.01)',
        (~np.isclose(number.TotalCharges, number.MonthlyCharges * number.TenureMonths,
                     atol=0.01, rtol=0) & number.notna().all(axis=1)).sum(), 'review')
    return pd.DataFrame(rows)


def require_valid(df: pd.DataFrame) -> pd.DataFrame:
    checks = validation_checks(df)
    failures = checks.loc[checks.status == 'FAIL', 'check'].tolist()
    if failures:
        raise ValueError('Data failed validation: ' + '; '.join(failures))
    return checks


def profile_columns(df: pd.DataFrame) -> pd.DataFrame:
    check_schema(df)
    return pd.DataFrame([
        {'column': c, 'dtype': str(df[c].dtype), 'missing': int(df[c].isna().sum()),
         'missing_pct': float(df[c].isna().mean() * 100),
         'unique_nonmissing': int(df[c].nunique()), 'definition': DEFINITIONS[c]}
        for c in COLUMNS
    ])


def iqr_audit(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in NUMERIC:
        values = pd.to_numeric(df[col], errors='coerce')
        q1, q3 = values.quantile([0.25, 0.75])
        low, high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        rows.append({'column': col, 'q1': q1, 'q3': q3, 'lower_fence': low,
                     'upper_fence': high, 'flagged_rows': int(((values < low) | (values > high)).sum())})
    return pd.DataFrame(rows)


def quality_summary(df: pd.DataFrame) -> dict:
    checks = validation_checks(df)
    return {'rows': len(df), 'columns': len(df.columns),
            'missing_cells': int(df.isna().sum().sum()),
            'exact_duplicates_excess': int(df.duplicated().sum()),
            'duplicate_IDs_excess': int(df.CustomerID.duplicated().sum()),
            'validation_error_violations': int(checks.loc[checks.severity == 'error', 'violations'].sum()),
            'IQR_flags_across_columns': int(iqr_audit(df).flagged_rows.sum())}
