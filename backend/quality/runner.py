"""Per-executable evidence; canonical procedures are never promoted to PASS."""
import hashlib
import json
import os
import platform
import subprocess
import time
import unittest
from datetime import datetime, timezone
from pathlib import Path
import django
from django.db import connection
from django.test.runner import DiscoverRunner

ROOT = Path(__file__).resolve().parents[2]


def git(*args):
    try:
        return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return 'unavailable'


def metadata():
    return {'revision': git('rev-parse', 'HEAD'), 'dirty': bool(git('status', '--porcelain')),
            'python': platform.python_version(), 'django': django.get_version(),
            'database_vendor': connection.vendor,
            'database_server_version': getattr(connection, 'pg_version', None) if connection.vendor == 'postgresql' else None}


class EvidenceResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        self.started_at = time.monotonic()

    def record(self, test, outcome, reason=None):
        entry = {'executable': test.id(), 'outcome': outcome,
                 'seconds': round(time.monotonic() - self.started_at, 6)}
        if reason:
            entry['reason'] = reason
        self.records.append(entry)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []
        self.started_at = time.monotonic()

    def addSuccess(self, test):
        super().addSuccess(test)
        self.record(test, 'passed')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.record(test, 'failed', err[0].__name__)

    def addError(self, test, err):
        super().addError(test, err)
        self.record(test, 'error', err[0].__name__)

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.record(test, 'skipped', reason)

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is not None:
            self.record(test, 'failed' if issubclass(err[0], test.failureException) else 'error', 'subtest failure')

    def addExpectedFailure(self, test, err):
        super().addExpectedFailure(test, err)
        self.record(test, 'expected_failure')

    def addUnexpectedSuccess(self, test):
        super().addUnexpectedSuccess(test)
        self.record(test, 'unexpected_success')


def build_report(records, build, mapping, successful, started):
    mapped = []
    for record in records:
        support = mapping.get(record['executable'], {})
        mapped.append(record | {'requirements': support.get('requirements', []),
                                'planned_ids': support.get('planned_ids', []),
                                'scope': support.get('scope', 'Unmapped executable; no canonical coverage claimed')})
    return {'schema_version': 1, 'started_utc': started,
            'finished_utc': datetime.now(timezone.utc).isoformat(), 'build': build,
            'successful': successful, 'executables': mapped,
            'canonical_case_results': 'Not Executed unless separately evidenced in manual execution records',
            'note': 'Passing automated subcases do not prove a full system/security procedure. Skips are not passes.'}


class EvidenceRunner(DiscoverRunner):
    def get_resultclass(self):
        return EvidenceResult

    def run_suite(self, suite, **kwargs):
        result = super().run_suite(suite, **kwargs)
        self.records = result.records
        self.successful = result.wasSuccessful()
        return result

    def run_tests(self, test_labels, **kwargs):
        if self.parallel > 1:
            raise ValueError('EvidenceRunner requires serial execution; omit --parallel')
        self.records, self.successful = [], False
        started = datetime.now(timezone.utc).isoformat()
        build = metadata()
        mapping_path = ROOT / 'quality' / 'executables.json'
        mapping = json.loads(mapping_path.read_text()) if mapping_path.exists() else {}
        try:
            return super().run_tests(test_labels, **kwargs)
        finally:
            report = build_report(self.records, build, mapping, self.successful, started)
            report['manifest_sha256'] = hashlib.sha256(mapping_path.read_bytes()).hexdigest() if mapping_path.exists() else None
            output = Path(os.environ.get('RMS_EVIDENCE_PATH', ROOT / 'test-results' / 'django.json'))
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(json.dumps(report, indent=2) + '\n')
