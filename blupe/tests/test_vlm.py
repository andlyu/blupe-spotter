"""HTTP contract checks; no real provider, images or robot commands are used."""
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from spotter_yam.vlm import VisionSupervisor


@contextmanager
def provider(content, status=200):
    calls = []

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            calls.append((self.command, self.path, self.headers,
                          json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
            self.send_response(status)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            payload = ({'choices': [{'message': {'content': json.dumps(content)}}]}
                       if status == 200 else {'error': {'message': 'secret-provider-body'}})
            self.wfile.write(json.dumps(payload).encode())

        def do_GET(self):
            calls.append((self.command, self.path, self.headers, None))
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"data":[{"id":"qwen38"}]}')

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield 'http://127.0.0.1:' + str(server.server_port) + '/v1', calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class ManagedSupervisorTests(unittest.TestCase):
    def test_openrouter_vision_request_preserves_cameras_and_enforces_parameters(self):
        with provider({'flag': False, 'risk': 0, 'why': 'progress'}) as (endpoint, calls):
            supervisor = VisionSupervisor(endpoint, 'qwen/qwen3.8-27b', 'test-key', api_style='openrouter')
            frames = [SimpleNamespace(name=name, jpeg=name.encode()) for name in ('top', 'left', 'right')]
            result = supervisor.screen('move the block', [{'chunk': 1, 'frames': frames}])
            self.assertFalse(result['flag'])
            method, path, headers, body = calls[0]
            self.assertEqual((method, path), ('POST', '/v1/chat/completions'))
            self.assertEqual(headers['Authorization'], 'Bearer test-key')
            self.assertEqual(body['model'], 'qwen/qwen3.8-27b')
            self.assertEqual(body['reasoning'], {'effort': 'none'})
            self.assertTrue(body['provider']['require_parameters'])
            self.assertEqual(body['response_format'], {'type': 'json_object'})
            self.assertNotIn('chat_template_kwargs', body)
            images = [item for item in body['messages'][1]['content'] if item['type'] == 'image_url']
            self.assertEqual(len(images), 3)
            self.assertEqual(images[0]['image_url']['url'], 'data:image/jpeg;base64,dG9w')

    def test_openrouter_readiness_checks_authenticated_inference_not_public_catalog(self):
        with provider({'ready': True}) as (endpoint, calls):
            VisionSupervisor(endpoint, 'qwen/qwen3.8-27b', 'test-key', api_style='openrouter').ready()
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], 'POST')
            self.assertEqual(calls[0][2]['Authorization'], 'Bearer test-key')
            self.assertLessEqual(calls[0][3]['max_tokens'], 64)

    def test_authentication_and_credit_errors_fail_without_retry_or_leaking_provider_body(self):
        for status, message in ((401, 'API key'), (402, 'credits')):
            with self.subTest(status=status), provider({}, status) as (endpoint, calls):
                supervisor = VisionSupervisor(endpoint, 'qwen/qwen3.8-27b', 'test-key', api_style='openrouter')
                with patch('spotter_yam.vlm.time.sleep', side_effect=AssertionError('Must not retry')):
                    with self.assertRaisesRegex(RuntimeError, message) as caught:
                        supervisor.ready()
                self.assertNotIn('secret-provider-body', str(caught.exception))
                self.assertNotIn('test-key', str(caught.exception))
                self.assertEqual(len(calls), 1)

    def test_readiness_rejects_wrong_response_and_cancellation(self):
        with provider({'ready': False}) as (endpoint, calls):
            supervisor = VisionSupervisor(endpoint, 'qwen/qwen3.8-27b', 'test-key', api_style='openrouter')
            with self.assertRaisesRegex(RuntimeError, 'readiness'):
                supervisor.ready()
            with self.assertRaisesRegex(RuntimeError, 'cancelled'):
                supervisor.ready(lambda: True)
            self.assertEqual(len(calls), 1)

    def test_vllm_discovery_and_request_remain_compatible(self):
        with provider({'verdict': 'pass'}) as (endpoint, calls):
            supervisor = VisionSupervisor(endpoint, 'qwen38', 'test-key')
            supervisor.ready()
            self.assertEqual(supervisor.judge('move', [], {}), {'verdict': 'pass'})
            self.assertEqual(calls[0][:2], ('GET', '/v1/models'))
            body = calls[1][3]
            self.assertEqual(body['chat_template_kwargs'], {'enable_thinking': False})
            self.assertNotIn('reasoning', body)
            self.assertNotIn('provider', body)

    def test_openrouter_requires_a_key_and_rejects_unknown_api_style(self):
        with self.assertRaisesRegex(ValueError, 'API key'):
            VisionSupervisor('https://openrouter.ai/api/v1', 'qwen/qwen3.8-27b', api_style='openrouter')
        with self.assertRaisesRegex(ValueError, 'API style'):
            VisionSupervisor('https://example.invalid/v1', 'model', api_style='typo')


if __name__ == '__main__':
    unittest.main()
