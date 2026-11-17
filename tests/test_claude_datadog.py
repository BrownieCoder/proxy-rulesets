"""Real ordered-domain regressions for the removed shared Datadog override."""
import json
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from siri_ai import DomainRules, entries

CLAUDE = '🧠 Claude'
REMOVED = 'DOMAIN-SUFFIX,datadoghq.com,' + CLAUDE
DATADOG = {'app.datadoghq.com', 'api.datadoghq.com',
           'agent-http-intake.logs.datadoghq.com'}
SUPPLEMENTS = {
    'DOMAIN,api.anthropic.com', 'DOMAIN,mcp-proxy.anthropic.com',
    'DOMAIN,platform.claude.com', 'DOMAIN-SUFFIX,anthropic.com',
    'DOMAIN-SUFFIX,claude.ai', 'DOMAIN-SUFFIX,claude.com',
    'DOMAIN-SUFFIX,claudeusercontent.com', 'DOMAIN-SUFFIX,modelcontextprotocol.io',
    'DOMAIN-SUFFIX,clau.de',
}
SECURITY = {('Privacy', 'REJECT'), ('Hijacking', '🚫 Hijacking')}


class ClaudeDatadogScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ordered = yaml.safe_load((ROOT / 'config/rules.yaml').read_text(encoding='utf-8'))['rules']
        manifests = {}
        for filename in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads((ROOT / filename).read_text(encoding='utf-8')))
        cls.payloads = {name: entries(ROOT / record['path']) for name, record in manifests.items()}
        cls.providers = {name: DomainRules(payload) for name, payload in cls.payloads.items()}

    def route(self, host, ordered=None, providers=None):
        for rule in self.ordered if ordered is None else ordered:
            fields = rule.split(',')
            kind = fields[0]
            if kind == 'RULE-SET':
                models = self.providers if providers is None else providers
                if models[fields[1]].matches(host):
                    return fields[1], fields[2]
            elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                if DomainRules([rule]).matches(host):
                    return ','.join(fields[:2]), fields[2]
            elif kind == 'MATCH':
                return kind, fields[1]
            else:
                self.assertIn(kind, {'GEOIP', 'IP-CIDR', 'IP-CIDR6'})
        self.fail('Missing MATCH rule')

    def previous_order(self):
        ordered = list(self.ordered)
        ordered.insert(ordered.index('RULE-SET,Google,🔎 Google'), REMOVED)
        return ordered

    def test_shared_root_is_not_bound_to_claude(self):
        self.assertNotIn(REMOVED, self.ordered)
        supplemental = {','.join(rule.split(',')[:2]) for rule in self.ordered
                        if rule.split(',')[0] in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}
                        and rule.split(',')[2] == CLAUDE}
        self.assertEqual(supplemental, SUPPLEMENTS)

    def test_actual_datadog_first_matches_are_not_claude(self):
        for host in DATADOG | {'datadoghq.com', 'http-intake.logs.us5.datadoghq.com'}:
            with self.subTest(host=host):
                # General providers and legitimate future security updates may change the fallback.
                self.assertNotEqual(self.route(host)[1], CLAUDE)

    def test_existing_claude_routes_are_preserved(self):
        for host in ('api.anthropic.com', 'mcp-proxy.anthropic.com', 'platform.claude.com',
                     'anthropic.com', 'claude.ai', 'claude.com', 'assets.claudeusercontent.com',
                     'modelcontextprotocol.io', 'clau.de'):
            with self.subTest(host=host):
                current = self.route(host)
                self.assertEqual(current, self.route(host, self.previous_order()))
                self.assertTrue(current in SECURITY or current[1] == CLAUDE)

    def test_non_datadog_routes_do_not_change(self):
        for host in ('browser-intake-us5-datadoghq.com', 'datadoghq.com.example.org',
                     'notdatadoghq.com', 'app.datadoghq.eu', 'www.goofish.com',
                     'www.youku.com', 'pan.baidu.com', 'www.taobao.com', 'v.qq.com',
                     'guzzoni.apple.com', 'hmma.baidu.com', 'hoyoverse.com',
                     'fastcdn.hoyoverse.com', 'cdn.usefathom.com', 'example.org'):
            with self.subTest(host=host):
                self.assertEqual(self.route(host), self.route(host, self.previous_order()))

    def test_security_priority_survives_for_shared_and_claude_hosts(self):
        hosts = DATADOG | {'api.anthropic.com', 'platform.claude.com'}
        for provider, target in SECURITY:
            models = dict(self.providers)
            models[provider] = DomainRules(self.payloads[provider] + ['DOMAIN,' + host for host in hosts])
            for host in hosts:
                with self.subTest(provider=provider, host=host):
                    expected = (('Privacy', 'REJECT') if models['Privacy'].matches(host)
                                else (provider, target))
                    self.assertEqual(self.route(host, providers=models), expected)
                    self.assertEqual(self.route(host, self.previous_order(), models), expected)

    def test_restoring_old_suffix_reproduces_the_misrouting(self):
        for host in DATADOG:
            with self.subTest(host=host):
                previous = self.route(host, self.previous_order())
                if previous in SECURITY:
                    self.assertEqual(self.route(host), previous)
                else:
                    self.assertEqual(previous, ('DOMAIN-SUFFIX,datadoghq.com', CLAUDE))
                    self.assertNotEqual(self.route(host)[1], CLAUDE)


if __name__ == '__main__':
    unittest.main()
