"""Validate the canonical inventory without claiming test execution."""
import hashlib
import json
from pathlib import Path


def validate(root):
    manifest = json.loads((root / 'quality/traceability.json').read_text())
    expected_requirements = {f'{prefix}-{i}' for prefix, end in [('REQ', 14), ('PERF', 3), ('SEC', 8), ('QA', 4)] for i in range(1, end + 1)}
    expected_tests = {f'{prefix}_{i:02}' for prefix, end in [('UT', 23), ('IT', 10), ('ST', 14), ('SV', 10), ('SR', 1)] for i in range(1, end + 1)}
    requirements, tests = manifest['requirements'], manifest['tests']
    assert len(requirements) == 29 and {r['id'] for r in requirements} == expected_requirements, 'Requirement inventory drift'
    assert len(tests) == 58 and {t['id'] for t in tests} == expected_tests, 'Canonical test inventory drift'
    for source in manifest['sources']:
        assert hashlib.sha256((root / source['path']).read_bytes()).hexdigest() == source['sha256'], f"Source changed: {source['path']}; review the RTM"
    by_test = {t['id']: t for t in tests}
    for requirement in requirements:
        assert requirement['tests'], f"Unmapped requirement {requirement['id']}"
        for test_id in requirement['tests']:
            assert test_id in by_test and requirement['id'] in by_test[test_id]['requirements'], 'Broken reciprocal mapping'
        for path in requirement['actual_paths']:
            assert (root / path).is_file(), f'Actual path absent: {path}'
    for test in tests:
        assert test['requirements'] or test.get('business_rule'), f"Orphan test {test['id']}"
        assert test['variants'] and 0 <= test['canonical_variant'] < len(test['variants'])
        assert test['result'] == 'Not Executed' or test['evidence'], 'Result requires execution evidence'
    print('Traceability valid: 29 requirements, 58 canonical cases, source digests and actual paths verified. No execution pass inferred.')


if __name__ == '__main__':
    validate(Path(__file__).resolve().parents[1])
