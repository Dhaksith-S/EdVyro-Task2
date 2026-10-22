"""Deterministic cleaning CLI. Raw input is never overwritten or fetched silently."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data_validation import CATEGORIES, INTEGERS, NUMERIC, check_schema, require_valid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RAW = ROOT / 'data/raw/customer_churn_sample.csv'
DEFAULT_CLEAN = ROOT / 'data/processed/customer_churn_cleaned.csv'


def load_data(path: str | Path = DEFAULT_RAW) -> pd.DataFrame:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f'Missing authorized dataset: {path.name}. See data/raw/README.md.')
    df = pd.read_csv(path, keep_default_na=True)
    check_schema(df)
    return df


def clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    check_schema(raw)
    df = raw.copy(deep=True)
    decisions = []

    def log(issue, detection, action, justification, affected, validation='PASS'):
        decisions.append(dict(issue=issue, detection_method=detection, action=action,
                              justification=justification, rows_affected=int(affected), validation_result=validation))

    for col in ['CustomerID', *CATEGORIES]:
        original = df[col].astype('string')
        trimmed = original.str.strip().replace('', pd.NA)
        changed = original.fillna('<NA>').ne(trimmed.fillna('<NA>'))
        if col in CATEGORIES:
            mapping = {v.casefold(): v for v in CATEGORIES[col]}
            normalized = trimmed.map(lambda x: mapping.get(x.casefold(), x) if pd.notna(x) else pd.NA)
            changed |= trimmed.fillna('<NA>').ne(normalized.fillna('<NA>'))
            trimmed = normalized
        text_dtype = raw[col].dtype if isinstance(raw[col].dtype, pd.StringDtype) else 'object'
        df[col] = trimmed.astype(text_dtype)
        log(f'{col}: formatting',
            'Compare trimmed identifier' if col == 'CustomerID' else 'Trim and case-insensitive comparison with supplied labels',
            'Trim identifier whitespace; blank to missing' if col == 'CustomerID' else 'Trim surrounding whitespace; canonicalize known labels; blank to missing',
            'Preserve identifier case and do not guess unknown categories.', changed.sum())
    for col in NUMERIC:
        parsed = pd.to_numeric(df[col], errors='raise')
        if col in INTEGERS:
            if (parsed.dropna().mod(1) != 0).any():
                raise ValueError(f'{col} contains fractional count/age values')
            parsed = parsed.astype('Int64') if parsed.isna().any() else parsed.astype('int64')
        else:
            parsed = parsed.astype('float64')
        changed = len(df) if str(df[col].dtype) != str(parsed.dtype) else 0
        df[col] = parsed
        log(f'{col}: numeric type', 'Parse numbers and check integer fields', 'Use explicit numeric dtype',
            'Invalid numeric text fails instead of becoming an imputed value.', changed)
    duplicate = df.duplicated()
    log('Exact duplicate records', 'All-column equality after canonicalization', 'Keep first exact record',
        'Only exact copies are removable; conflicting customer IDs fail validation.', duplicate.sum())
    df = df.loc[~duplicate].reset_index(drop=True)
    require_valid(df)
    log('Missing or invalid required values', 'Required-field and domain checks', 'No imputation; fail if unresolved',
        'No defensible replacement is supplied; never infer a missing target.', 0)
    log('IQR extremes and billing review', '1.5 x IQR; age/tenure and billing consistency diagnostics',
        'Retain records; flag review checks without rewriting values',
        'Statistical extremes and billing deviations alone do not prove errors.', 0)
    return df, pd.DataFrame(decisions)


def run(raw_path: Path = DEFAULT_RAW, output_path: Path = DEFAULT_CLEAN) -> tuple[pd.DataFrame, pd.DataFrame]:
    if raw_path.resolve() == output_path.resolve():
        raise ValueError('Output must differ from raw input.')
    clean, log = clean_data(load_data(raw_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    clean.to_csv(output_path, index=False, lineterminator='\n', float_format='%.2f')
    # Check the actual delivered serialization, including cent precision.
    pd.testing.assert_frame_equal(clean, load_data(output_path), check_dtype=False)
    return clean, log


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, default=DEFAULT_RAW)
    parser.add_argument('--output', type=Path, default=DEFAULT_CLEAN)
    args = parser.parse_args()
    clean, log = run(args.input, args.output)
    (ROOT / 'reports').mkdir(exist_ok=True)
    log.to_csv(ROOT / 'reports/cleaning_decisions.csv', index=False)
    print(f'Validated and exported {len(clean)} rows to {args.output.name}')
