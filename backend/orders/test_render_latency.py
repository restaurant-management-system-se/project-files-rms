"""RMS-25 / #28: actual Chromium DOM paint after committed status change.
RMS_RUN_BROWSER=1 python manage.py test orders.test_render_latency -v2
Prerequisites: pip install playwright; playwright install chromium; realtime npm ci.
20 real PostgreSQL transitions, actual Django/Node and same-origin proxy.
"""
import json
import math
import os
import platform
import subprocess
import time
from pathlib import Path
from unittest import skipUnless
from unittest.mock import patch
from django.conf import settings
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.db import connection
from django.test import Client, override_settings
from accounts.models import User
from .models import Order
from .services import change_status
from .events import dispatch_event

# Ephemeral test-only same-origin HTTP/WS proxy; no production deployment claim.
PROXY = r'''
const http=require('node:http'),net=require('node:net');
const django=new URL(process.env.TEST_DJANGO),node=new URL(process.env.TEST_NODE);
const target=url=>url.startsWith('/socket.io')?node:django;
const server=http.createServer((req,res)=>{
 const t=target(req.url),up=http.request({hostname:t.hostname,port:t.port,path:req.url,method:req.method,headers:req.headers},r=>{res.writeHead(r.statusCode,r.headers);r.pipe(res);});
 up.on('error',()=>{res.writeHead(502);res.end();});req.pipe(up);
});
server.on('upgrade',(req,socket,head)=>{
 const t=target(req.url),up=net.connect(Number(t.port),t.hostname,()=>{
  up.write(req.method+' '+req.url+' HTTP/'+req.httpVersion+'\r\n'+Object.entries(req.headers).map(([k,v])=>k+': '+v).join('\r\n')+'\r\n\r\n');
  if(head.length)up.write(head);socket.pipe(up);up.pipe(socket);
 });up.on('error',()=>socket.destroy());socket.on('error',()=>up.destroy());
});server.listen(0,'127.0.0.1',()=>console.log(JSON.stringify({port:server.address().port})));
'''


@skipUnless(os.environ.get('RMS_RUN_BROWSER') == '1', 'Opt-in real Chromium render measurement')
@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'], RMS_REALTIME_KEY='ephemeral-latency-key-at-least-32-characters')
class RenderLatencyTests(StaticLiveServerTestCase):
    def test_it07_commit_to_customer_paint(self):
        from playwright.sync_api import sync_playwright
        self.assertEqual(connection.vendor, 'postgresql')
        root = Path(settings.BASE_DIR).parent
        owner = User.objects.create_user(username='latency-owner', email='latency-owner@example.invalid')
        staff = User.objects.create(username='latency-staff', email='latency-staff@example.invalid', role='Staff')
        client = Client(); client.force_login(owner, backend='accounts.authentication.IdentifierBackend')
        session = client.session; session['last_activity'] = time.time(); session.save()
        node = proxy = None
        observations = []
        try:
            # Proxy must start first to establish the exact Origin used by Node.
            proxy = subprocess.Popen(['node', '-e', PROXY], env=os.environ | {'TEST_DJANGO': self.live_server_url, 'TEST_NODE': 'http://127.0.0.1:1'}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            # Restart proxy with a known Node port after initial allocation.
            proxy_port = json.loads(proxy.stdout.readline())['port']
            proxy.terminate(); proxy.wait(timeout=5)
            # Bind the allocated proxy port explicitly for Origin stability.
            fixed_proxy = PROXY.replace("server.listen(0,'127.0.0.1'", "server.listen(" + str(proxy_port) + ",'127.0.0.1'")
            origin = f'http://127.0.0.1:{proxy_port}'
            node = subprocess.Popen(['node', 'server.js'], cwd=root / 'realtime', env=os.environ | {'PORT': '0', 'RMS_REALTIME_KEY': settings.RMS_REALTIME_KEY, 'RMS_DJANGO_URL': self.live_server_url, 'RMS_PUBLIC_ORIGIN': origin}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            node_port = json.loads(node.stdout.readline())['port']
            proxy = subprocess.Popen(['node', '-e', fixed_proxy], env=os.environ | {'TEST_DJANGO': self.live_server_url, 'TEST_NODE': f'http://127.0.0.1:{node_port}'}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(json.loads(proxy.stdout.readline())['port'], proxy_port)
            with sync_playwright() as pw:
                browser = pw.chromium.launch()
                context = browser.new_context()
                context.add_cookies([{'name': settings.SESSION_COOKIE_NAME, 'value': client.cookies[settings.SESSION_COOKIE_NAME].value, 'url': origin}])
                page = context.new_page()
                # Mutation + two animation frames confirms a rendering opportunity,
                # not merely event receipt or assignment of textContent.
                page.add_init_script("""addEventListener('DOMContentLoaded',()=>{
                  window.rmsPainted=0;
                  new MutationObserver(()=>{const e=document.getElementById('tracking');
                    const v=Number(e.dataset.version||0);
                    requestAnimationFrame(()=>requestAnimationFrame(()=>window.rmsPainted=Math.max(window.rmsPainted,v)));
                  }).observe(document.getElementById('status'),{childList:true,subtree:true,characterData:true});
                });""")
                for index in range(10):
                    order = Order.objects.create(customer=owner, total_amount='0')
                    page.goto(origin + f'/orders/{order.pk}/')
                    page.wait_for_function("document.getElementById('connection').textContent==='Live updates connected'", timeout=10000)
                    for version, status in [(2, 'Preparing'), (3, 'Served')]:
                        committed = []
                        def timed_dispatch(event_id):
                            # dispatch_event is called by transaction.on_commit, so this
                            # common-process monotonic timestamp is strictly after commit.
                            committed.append(time.perf_counter_ns())
                            return dispatch_event(event_id)
                        with self.settings(RMS_REALTIME_INTERNAL_URL=f'http://127.0.0.1:{node_port}'):
                            with patch('orders.events.dispatch_event', side_effect=timed_dispatch):
                                change_status(user=staff, order_id=order.pk, status=status, expected_version=version - 1)
                        self.assertEqual(len(committed), 1)
                        page.wait_for_function('(v)=>window.rmsPainted>=v', arg=version, timeout=10000)
                        elapsed = (time.perf_counter_ns() - committed[0]) / 1e6
                        self.assertEqual(page.locator('#status').inner_text(), status)
                        observations.append({'order_id': order.pk, 'version': version, 'status': status, 'elapsed_ms_upper_bound': elapsed, 'within_1s': elapsed <= 1000})
                # RMS-19 integration: Node outage cannot undo saved business state.
                recovery = Order.objects.create(customer=owner, total_amount='0')
                page.goto(origin + f'/orders/{recovery.pk}/')
                page.wait_for_function("document.getElementById('connection').textContent==='Live updates connected'", timeout=10000)
                node.terminate(); node.wait(timeout=5)
                change_status(user=staff, order_id=recovery.pk, status='Preparing', expected_version=1)
                page.wait_for_function("document.getElementById('status').textContent==='Preparing'", timeout=10000)
                node = subprocess.Popen(['node', 'server.js'], cwd=root / 'realtime', env=os.environ | {'PORT': str(node_port), 'RMS_REALTIME_KEY': settings.RMS_REALTIME_KEY, 'RMS_DJANGO_URL': self.live_server_url, 'RMS_PUBLIC_ORIGIN': origin}, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                self.assertEqual(json.loads(node.stdout.readline())['port'], node_port)
                page.wait_for_function("document.getElementById('connection').textContent==='Live updates connected'", timeout=15000)
                with self.settings(RMS_REALTIME_INTERNAL_URL=f'http://127.0.0.1:{node_port}'):
                    change_status(user=staff, order_id=recovery.pk, status='Served', expected_version=2)
                page.wait_for_function("document.getElementById('status').textContent==='Served'", timeout=10000)
                # Idle expiry is rejected by the running server and the UI stops
                # automatically resubscribing until a fresh login/page load.
                from django.contrib.sessions.backends.db import SessionStore
                expired = SessionStore(session_key=session.session_key)
                expired['last_activity'] = time.time() - settings.SESSION_IDLE_TIMEOUT - 10
                expired.save()
                page.wait_for_function("document.getElementById('connection').textContent.includes('Log in again')", timeout=10000)
                report_reconnect = {'node_restart': True, 'missed_state_via_REST': True, 'resubscribed_live_delivery': True, 'expired_session_requires_login': True}
                (root / 'test-results').mkdir(exist_ok=True)
                (root / 'test-results' / 'RMS-19-browser-reconnect.json').write_text(json.dumps(report_reconnect, indent=2))
                browser.close()
        finally:
            for process in (proxy, node):
                if process:
                    process.terminate()
                    try: process.wait(timeout=5)
                    except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=5)
            target = root / 'test-results'; target.mkdir(exist_ok=True)
            values = sorted(row['elapsed_ms_upper_bound'] for row in observations)
            report = {'issue': 28, 'test': 'IT_07 / ST_05', 'clock': 'One Python perf_counter_ns clock, after transaction.on_commit to Chromium two-frame acknowledgement; includes IPC acknowledgement overhead (conservative upper bound)', 'platform': platform.platform(), 'browser': 'Chromium headless, local test environment', 'sample_count': len(values), 'p95_ms_nearest_rank': values[math.ceil(.95 * len(values)) - 1] if values else None, 'within_1s_count': sum(row['within_1s'] for row in observations), 'PERF_2_pass': len(values) == 20 and sum(row['within_1s'] for row in observations) >= 19, 'REQ_10_each_update_pass_for_this_sample_only': len(values) == 20 and all(row['within_1s'] for row in observations), 'observations': observations}
            (target / 'RMS-25-render-latency.json').write_text(json.dumps(report, indent=2))
        self.assertEqual(len(observations), 20)
        self.assertGreaterEqual(sum(row['within_1s'] for row in observations), 19)
