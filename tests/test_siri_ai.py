"""针对空集、生成漂移与 first-match 退化的离线回归测试。"""
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import siri_ai


class SiriAIContract(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ('rules', 'ruleset', 'config'):
            shutil.copytree(ROOT / name, self.root / name)
        (self.root / 'research').mkdir()
        for name in ('sources.json', 'local-rulesets.json', 'research/SiriAI-audit.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def check_rejected(self):
        with self.assertRaises(ValueError):
            with contextlib.redirect_stdout(io.StringIO()):
                siri_ai.validate(self.root)

    def test_current_public_routing(self):
        with contextlib.redirect_stdout(io.StringIO()):
            siri_ai.validate(self.root)

    def test_invalid_domain_forms(self):
        path = self.root / 'rules/siri-ai-domains.txt'
        for value in ('', '*.apple.com\n', 'DOMAIN,apple.com\n', 'Bad.apple.com\n', '-bad.apple.com\n', 'a..apple.com\n', '192.0.2.1\n'):
            with self.subTest(value=value):
                path.write_text(value)
                self.check_rejected()

    def test_duplicate(self):
        path = self.root / 'rules/siri-ai-domains.txt'
        path.write_text(path.read_text() + 'guzzoni.apple.com\n')
        self.check_rejected()

    def test_generated_drift(self):
        path = self.root / 'ruleset/SiriAI.yaml'
        path.write_text(path.read_text().replace('DOMAIN,', 'DOMAIN-SUFFIX,', 1))
        self.check_rejected()

    def test_provenance_drift(self):
        path = self.root / 'rules/siri-ai-provenance.json'
        records = json.loads(path.read_text())
        records[0]['source'] = 'https://example.org/unverified'
        path.write_text(json.dumps(records))
        self.check_rejected()

    def test_apple_preemption(self):
        path = self.root / 'config/rules.yaml'
        siri = '  - RULE-SET,SiriAI,🤖 AI 服务\n'
        text = path.read_text().replace(siri, '')
        path.write_text(text.replace('  - RULE-SET,Apple,🍎 Apple\n', '  - RULE-SET,Apple,🍎 Apple\n' + siri))
        self.check_rejected()

    def test_new_earlier_security_match_detected(self):
        path = self.root / 'ruleset/Privacy_No_Resolve.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,guzzoni.apple.com\n')
        self.check_rejected()

    def test_missing_provider_reference(self):
        path = self.root / 'config/rule-providers.local.yaml'
        path.write_text(path.read_text().replace('  SiriAI:', '  Unknown:'))
        self.check_rejected()

    def test_wrong_policy_reference(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text().replace('RULE-SET,SiriAI,🤖 AI 服务', 'RULE-SET,SiriAI,Undefined'))
        self.check_rejected()

    def test_exact_does_not_match_child(self):
        rules = siri_ai.DomainRules(['DOMAIN,apple-relay.cloudflare.com'])
        self.assertTrue(rules.matches('apple-relay.cloudflare.com'))
        self.assertFalse(rules.matches('child.apple-relay.cloudflare.com'))
        self.assertFalse(rules.matches('cloudflare.com'))


if __name__ == '__main__':
    unittest.main()
