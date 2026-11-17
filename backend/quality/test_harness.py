"""H_ checks validate shared support; source IDs remain separate procedures."""
import ast
import io
import unittest
from pathlib import Path
from django.conf import settings
from django.test import SimpleTestCase, TestCase, override_settings
from quality.fixtures import SessionClient, auth_clock, role_users
from quality.runner import EvidenceResult, build_report


class ModuleBoundaryTests(SimpleTestCase):
    def test_SR_01_no_cross_app_view_imports(self):
        apps = {'accounts', 'booking', 'menu', 'orders'}
        violations = []
        for app in apps:
            for path in (Path(settings.BASE_DIR) / app).rglob('*.py'):
                for node in ast.walk(ast.parse(path.read_text())):
                    names = []
                    if isinstance(node, ast.Import):
                        names = [alias.name for alias in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0:
                        names = [node.module or ''] + [f'{node.module}.{alias.name}' for alias in node.names]
                    for name in names:
                        bits = name.split('.')
                        if bits[0] in apps - {app} and 'views' in bits[1:]:
                            violations.append(f'{path.relative_to(settings.BASE_DIR)}:{node.lineno} imports {name}')
        self.assertEqual(violations, [])

    def test_H_01_evidence_keeps_failure_skip_and_success_distinct(self):
        class Representative(unittest.TestCase):
            def test_pass(self): self.assertTrue(True)
            def test_fail(self): self.fail('intentional harness self-check')
            @unittest.skip('intentional pending example')
            def test_pending(self): pass
        result = unittest.TextTestRunner(stream=io.StringIO(), resultclass=EvidenceResult).run(
            unittest.defaultTestLoader.loadTestsFromTestCase(Representative))
        self.assertFalse(result.wasSuccessful())
        self.assertEqual(sorted(r['outcome'] for r in result.records), ['failed', 'passed', 'skipped'])
        report = build_report(result.records, {'revision': 'self-check'}, {}, False, 'self-check')
        self.assertFalse(report['successful'])
        self.assertTrue(all(r['planned_ids'] == [] for r in report['executables']))
        self.assertIn('Not Executed', report['canonical_case_results'])


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class SharedFlowTests(TestCase):
    def test_H_02_real_login_role_fixture_and_exact_idle_boundary(self):
        users = role_users()
        self.assertEqual({u.role for u in users.values()}, {'Customer', 'Staff', 'Admin'})
        client = SessionClient()
        with auth_clock(100000):
            response = client.json_write('post', '/api/auth/login',
                                         {'identifier': users['Customer'].email, 'password': 'Harness#72'})
            self.assertEqual(response.status_code, 200, response.content)
        with auth_clock(101799):
            self.assertEqual(client.get('/api/auth/session').status_code, 200)
        with auth_clock(101800):
            self.assertEqual(client.get('/api/auth/session').status_code, 401)

    def test_H_03_registered_customer_reads_own_empty_resources_then_logs_out(self):
        client = SessionClient()
        self.assertEqual(client.json_write('post', '/api/auth/register', {
            'name': 'Flow Customer', 'email': 'flow@example.invalid', 'password': 'Cedar#29'}).status_code, 201)
        self.assertEqual(client.json_write('post', '/api/auth/login', {
            'identifier': 'flow@example.invalid', 'password': 'Cedar#29'}).status_code, 200)
        for path in ['/api/bookings', '/api/orders']:
            response = client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), [])
        self.assertEqual(client.json_write('post', '/api/auth/logout', {}).status_code, 204)
        self.assertEqual(client.get('/api/orders').status_code, 401)
