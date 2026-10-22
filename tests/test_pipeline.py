"""Meaningful input fault tests and end-to-end artifact consistency checks."""
import hashlib
import json
from pathlib import Path
import re

import nbformat
import numpy as np
import pandas as pd
import pytest
from PIL import Image

from src.data_cleaning import ROOT, DEFAULT_RAW, clean_data, load_data, run
from src.data_validation import COLUMNS, NUMERIC, iqr_audit, require_valid
from src.analysis import FIGURES, summary_metrics


@pytest.fixture
def raw():
    return load_data()


def test_authorized_input_integrity(raw):
    source = json.loads((ROOT / 'src/provenance.json').read_text())
    assert hashlib.sha256(DEFAULT_RAW.read_bytes()).hexdigest() == source['source_sha256']
    assert raw.shape == (source['expected_rows'], source['expected_columns'])
    assert list(raw.columns) == COLUMNS


def test_missing_file_is_actionable(tmp_path):
    with pytest.raises(FileNotFoundError, match='authorized dataset'):
        load_data(tmp_path / 'missing.csv')


def test_schema_rejected(raw):
    with pytest.raises(ValueError, match='ordered columns'):
        clean_data(raw.drop(columns='Age'))


def test_clean_preserves_all_source_values_and_input(raw):
    original = raw.copy(deep=True)
    clean, decisions = clean_data(raw)
    pd.testing.assert_frame_equal(raw, original)
    pd.testing.assert_frame_equal(clean, original, check_dtype=False)
    assert decisions.rows_affected.sum() == 0
    assert clean.Churn.value_counts().to_dict() == {'No': 8, 'Yes': 7}


def test_idempotent_and_deterministic(raw, tmp_path):
    clean, _ = clean_data(raw)
    twice, _ = clean_data(clean)
    pd.testing.assert_frame_equal(clean, twice)
    first, second = tmp_path / 'a.csv', tmp_path / 'b.csv'
    run(DEFAULT_RAW, first)
    run(DEFAULT_RAW, second)
    assert first.read_bytes() == second.read_bytes()
    pd.testing.assert_frame_equal(clean, load_data(first), check_dtype=False)


def test_refuse_raw_overwrite():
    with pytest.raises(ValueError, match='differ'):
        run(DEFAULT_RAW, DEFAULT_RAW)


def test_exact_duplicate_removed(raw):
    duplicated = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
    clean, log = clean_data(duplicated)
    pd.testing.assert_frame_equal(clean, raw, check_dtype=False)
    assert log.loc[log.issue.eq('Exact duplicate records'), 'rows_affected'].iloc[0] == 1


def test_conflicting_customer_ids_rejected(raw):
    raw.loc[1, 'CustomerID'] = raw.loc[0, 'CustomerID']
    with pytest.raises(ValueError, match='Duplicate customer IDs'):
        clean_data(raw)


def test_known_formatting_corrected(raw):
    raw.loc[0, 'Churn'] = ' yes '
    raw.loc[0, 'CustomerID'] = ' ' + raw.loc[0, 'CustomerID'] + ' '
    clean, log = clean_data(raw)
    assert clean.loc[0, 'Churn'] == 'Yes'
    assert clean.loc[0, 'CustomerID'].strip() == clean.loc[0, 'CustomerID']
    assert log.rows_affected.sum() == 2


@pytest.mark.parametrize('column,value,match', [
    ('Churn', None, 'Missing required'), ('Churn', ' ', 'Missing required'),
    ('Churn', 'Maybe', 'Churn:'), ('ContractType', 'Quarterly', 'ContractType:'),
    ('CustomerID', 'invalid', 'Identifier format'), ('MonthlyCharges', -1., 'Negative'),
    ('MonthlyCharges', float('inf'), 'Nonfinite'), ('Age', -1, 'Negative'),
    ('TotalCharges', float('nan'), 'Missing required'),
])
def test_invalid_required_values_fail(raw, column, value, match):
    raw.loc[0, column] = value
    with pytest.raises(ValueError, match=match):
        clean_data(raw)


def test_invalid_numeric_text_fails(raw):
    raw['MonthlyCharges'] = raw.MonthlyCharges.astype('object')
    raw.loc[0, 'MonthlyCharges'] = 'not a number'
    with pytest.raises(ValueError):
        clean_data(raw)


def test_fractional_count_fails(raw):
    raw['SupportTickets'] = raw.SupportTickets.astype('float64')
    raw.loc[0, 'SupportTickets'] = 1.5
    with pytest.raises(ValueError, match='fractional'):
        clean_data(raw)


def test_outlier_preserved_and_review_is_visible(raw):
    raw.loc[0, 'TotalCharges'] = 1e6
    clean, _ = clean_data(raw)
    assert len(clean) == len(raw)
    assert clean.loc[0, 'TotalCharges'] == 1e6
    assert iqr_audit(clean).flagged_rows.sum() > 0
    assert require_valid(clean).status.eq('REVIEW').any()


def test_target_review_does_not_invent_population_threshold(raw):
    raw['Churn'] = 'No'
    checks = require_valid(raw)
    assert checks.loc[checks['check'].eq('Both churn classes present'), 'status'].iloc[0] == 'REVIEW'


def test_report_metrics_and_export_agree(raw):
    clean = load_data(ROOT / 'data/processed/customer_churn_cleaned.csv')
    assert summary_metrics(clean) == json.loads((ROOT / 'reports/metrics.json').read_text())
    comparison = pd.read_csv(ROOT / 'reports/quality_comparison.csv').set_index('metric')
    assert comparison.loc['rows', 'after'] == len(raw) == len(clean)
    checks = pd.read_csv(ROOT / 'reports/validation_results.csv')
    assert checks.status.eq('PASS').all()
    stats = pd.read_csv(ROOT / 'reports/summary_statistics.csv').set_index('column')
    np.testing.assert_allclose(stats['mean'], clean[NUMERIC].mean(), atol=1e-6)
    for filename in ['executive_summary.md', 'data_quality_report.md']:
        report = (ROOT / 'reports' / filename).read_text(encoding='utf-8')
        assert '7/15' in report and '46.7%' in report
        assert 'pending' in report.lower()


def test_notebook_executed_and_contains_no_record_ids():
    path = ROOT / 'notebooks/customer_churn_eda.ipynb'
    nb = nbformat.read(path, as_version=4)
    nbformat.validate(nb)
    code = [c for c in nb.cells if c.cell_type == 'code']
    assert code and all(c.execution_count is not None for c in code)
    assert all(o.output_type != 'error' for c in code for o in c.outputs)
    assert not re.search(r'CUST-\d+', path.read_text(encoding='utf-8'))
    assert not any('warning' in o.get('text', '').lower() for c in code for o in c.outputs)


@pytest.mark.parametrize('filename', FIGURES)
def test_figure_integrity(filename):
    with Image.open(ROOT / 'figures' / filename) as img:
        assert img.format == 'PNG'
        assert img.width >= 1500 and img.height >= 900
        img.verify()


def test_markdown_local_references_resolve():
    for path in [ROOT / 'README.md', *list((ROOT / 'reports').glob('*.md'))]:
        content = path.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)', content):
            if not target.startswith(('http:', 'https:', '#')):
                assert (path.parent / target.split('#')[0]).exists(), (path.name, target)
