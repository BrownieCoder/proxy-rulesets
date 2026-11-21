"""Dewu's exact portal boundaries on disposable copies of the public tree."""
import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import validate
from generate_catalog import generate
from siri_ai import DomainRules

HOSTS = {'dewu.com', 'www.dewu.com'}
TARGET = '👟 得物'
CONTROLS = {
    'agreement.dewu.com', 'cdn.dewu.com', 'cdn-fast.dewu.com', 'www.dewucdn.com', 'www.poizon.com',
    'open.dewu.com', 'stark.dewu.com', 'creator.dewu.com', 'livemcn.dewu.com',
    'liveplatform.dewu.com', 'mcn.dewu.com', 'poizon.jobs.feishu.cn',
    'www.weibo.com', 'www.xiaohongshu.com', 'www.taobao.com', 'www.bilibili.com',
    'www.google.com', 'hmma.baidu.com', 'fastcdn.hoyoverse.com', 'guzzoni.apple.com', 'example.org',
}
MARKER = f'  - RULE-SET,Dewu,{TARGET}\n'
GROUP = (
    f'  - name: "{TARGET}"\n'
    '    type: select\n'
    '    proxies:\n'
    '      - DIRECT\n'
    '      - "🚀 节点选择"\n'
    '      - "🧭 Final"\n'
)


class DewuContract(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        for name in ('config', 'ruleset', 'catalog', 'rules', 'research', 'services'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json', 'README.md'):
            shutil.copyfile(ROOT / name, self.root / name)

    def read(self, name):
        return (self.root / name).read_text(encoding='utf-8')

    def write(self, name, text):
        (self.root / name).write_text(text, encoding='utf-8')

    def validate_tree(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(validate.validate_tree(self.root), 0)

    def rejected(self, direct_reason, tree_reason=None):
        with self.assertRaisesRegex(ValueError, direct_reason):
            validate.validate_dewu(self.root)
        if tree_reason is not None:
            with self.assertRaisesRegex(ValueError, tree_reason):
                validate.validate_tree(self.root)

    def test_complete_fixture_and_tree_hook(self):
        validate.validate_dewu(self.root)
        self.validate_tree()
        with patch.object(validate, 'validate_dewu', side_effect=ValueError('Dewu gate active')) as gate:
            with self.assertRaisesRegex(ValueError, '^Dewu gate active$'):
                validate.validate_tree(self.root)
        gate.assert_called_once_with(self.root)

    def test_exact_public_baseline_and_new_first_matches(self):
        manifests = {}
        for filename in ('sources.json', 'local-rulesets.json'):
            manifests.update(json.loads(self.read(filename)))
        models = {name: DomainRules(yaml.safe_load(self.read(row['path']))['payload'])
                  for name, row in manifests.items()}
        rules = yaml.safe_load(self.read('config/rules.yaml'))['rules']

        def route(host, include_dewu=True):
            for rule in rules:
                kind, value, *policy = rule.split(',')
                if kind == 'RULE-SET':
                    if (include_dewu or value != 'Dewu') and models[value].matches(host):
                        return value, policy[0]
                elif kind in {'DOMAIN', 'DOMAIN-SUFFIX', 'DOMAIN-KEYWORD'}:
                    if DomainRules([rule]).matches(host):
                        return kind + ',' + value, policy[0]
                elif kind == 'MATCH':
                    return kind, value
                else:
                    self.assertIn(kind, {'GEOIP', 'IP-CIDR', 'IP-CIDR6'})
            self.fail('Missing MATCH')

        self.assertEqual(validate.DEWU_HOSTS, HOSTS)
        self.assertLessEqual(CONTROLS, validate.DEWU_CONTROLS)
        self.assertEqual(yaml.safe_load(self.read('ruleset/Dewu.yaml'))['payload'],
                         ['DOMAIN,dewu.com', 'DOMAIN,www.dewu.com'])
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertEqual(route(host, False), ('ChinaMax', '🇨🇳 China-Global'))
                self.assertEqual(route(host), ('Dewu', TARGET))
        shapes = {value for host in HOSTS for value in
                  ('child.' + host, 'not' + host, host + '.example.org')}
        for host in CONTROLS | shapes:
            with self.subTest(control=host):
                self.assertFalse(models['Dewu'].matches(host))
                self.assertEqual(route(host), route(host, False))

    def test_payload_stays_exact_and_rejects_yaml_override(self):
        path = 'ruleset/Dewu.yaml'
        original = self.read(path)
        variants = (
            (original.replace('  - DOMAIN,dewu.com\n', ''), 'two reviewed exact hosts', 'two reviewed exact hosts'),
            (original.replace('DOMAIN,dewu.com', 'DOMAIN-SUFFIX,dewu.com'),
             'two reviewed exact hosts', 'two reviewed exact hosts'),
            (original.replace('DOMAIN,www.dewu.com', 'DOMAIN,cdn.dewu.com'),
             'two reviewed exact hosts', 'two reviewed exact hosts'),
            (original + '  - DOMAIN,dewu.com\n',
             'Empty or duplicate rules', 'Dewu: local ruleset contains duplicate entries'),
            (original + 'payload: []\n', 'Expected one payload mapping', None),
        )
        for text, reason, tree_reason in variants:
            with self.subTest(text=text):
                self.write(path, text)
                self.rejected(reason, tree_reason)

    def test_unique_dedicated_reference(self):
        path = 'config/rules.yaml'
        original = self.read(path)
        for changed in (original.replace(MARKER, ''), original.replace(MARKER, MARKER * 2, 1),
                        original.replace(MARKER, '  - RULE-SET,Dewu,DIRECT\n')):
            with self.subTest(changed=changed.count(MARKER)):
                self.write(path, changed)
                self.rejected('exactly one dedicated policy reference', 'exactly one dedicated policy reference')

    def test_order_preserves_prior_app_and_broader_fallback(self):
        path = 'config/rules.yaml'
        original = self.read(path)
        for template, reason in (
            ('RULE-SET,Privacy,REJECT', 'Security and gaming rules must precede Dewu'),
            ('RULE-SET,ChinaGaming,DIRECT', 'Security and gaming rules must precede Dewu'),
            ('RULE-SET,Weibo,🟠 微博', 'invalid routing position relative to Weibo'),
            ('RULE-SET,WeChat,💬 微信', 'invalid routing position relative to WeChat'),
        ):
            with self.subTest(before=template):
                row = '  - ' + template + '\n'
                self.write(path, original.replace(MARKER, '').replace(row, MARKER + row))
                self.rejected(reason, reason)
        for template, reason in (
            ('RULE-SET,SiriAI,🤖 AI 服务', 'invalid routing position relative to SiriAI'),
            ('RULE-SET,Apple,🍎 Apple', 'invalid routing position relative to SiriAI'),
            ('RULE-SET,ChinaMax,🇨🇳 China-Global', 'invalid routing position relative to SiriAI'),
        ):
            with self.subTest(after=template):
                row = '  - ' + template + '\n'
                self.write(path, original.replace(MARKER, '').replace(row, row + MARKER))
                self.rejected(reason, reason)

    def test_group_requires_direct_first_select_with_both_options(self):
        path = 'config/proxy-groups.yaml'
        original = self.read(path)
        for group in (GROUP.replace('select', 'fallback'),
                      GROUP.replace('      - DIRECT\n', '') + '      - DIRECT\n',
                      GROUP.replace('      - "🚀 节点选择"\n', ''),
                      GROUP.replace('      - "🧭 Final"\n', ''),
                      GROUP.replace('    type: select\n', '    type: select\n    lazy: true\n')):
            with self.subTest(group=group):
                self.write(path, original.replace(GROUP, group))
                self.rejected('Dewu must be a DIRECT-first select', 'Dewu must be a DIRECT-first select')
        self.write(path, original.replace(GROUP, ''))
        self.rejected('Dewu must be a DIRECT-first select', 'references undefined policy groups')

    def test_final_cycle_and_missing_group_fail_both_validation_entries(self):
        path = "config/proxy-groups.yaml"
        original = self.read(path)
        final = '  - name: "🧭 Final"\n    type: select\n    proxies:\n'
        self.assertEqual(original.count(final), 1)
        for member, reason in ((TARGET, "contains a group cycle"),
                               ("MissingPublicGroup", "references undefined groups")):
            with self.subTest(member=member):
                self.write(path, original.replace(final, final + f'      - "{member}"\n', 1))
                for gate in (validate.validate_dewu, validate.validate_tree):
                    with self.subTest(gate=gate.__name__), self.assertRaisesRegex(ValueError, reason):
                        gate(self.root)

    def test_legal_literal_group_forms_use_public_model(self):
        path = 'config/proxy-groups.yaml'
        original = self.read(path)
        group = GROUP.replace(f'- name: "{TARGET}"', f"- name: '{TARGET}' # comment")
        group = group.replace('type: select', '"type": "select" # literal')
        self.write(path, original.replace(GROUP, group).replace('\n', '\r\n'))
        validate.validate_dewu(self.root)
        self.validate_tree()

    def test_duplicate_yaml_roots_fail_closed(self):
        for path, root_key in (('config/rules.yaml', 'rules'), ('config/proxy-groups.yaml', 'proxy-groups')):
            original = self.read(path)
            with self.subTest(path=path):
                self.write(path, original + '\n' + root_key + ': []\n')
                reason = r'Public ' + path.replace('.', r'\.')
                self.rejected(reason, reason)
            self.write(path, original)

    def test_unknown_provider_and_malformed_top_level_conditions(self):
        path = 'config/rules.yaml'
        original = self.read(path)
        for row, reason, tree_reason in (
            ('RULE-SET,MissingDewu,DIRECT', 'Dewu routing references missing provider: MissingDewu',
             'rules.yaml references undefined providers'),
            ('PROCESS-NAME,example,DIRECT', 'Unsupported top-level rule in Dewu domain-only model: PROCESS-NAME',
             'Unsupported top-level rule'),
            ('DOMAIN,dewu.com', 'Dewu domain-only model requires complete supported rules: DOMAIN', None),
            ('DOMAIN, dewu.com,DIRECT', 'routing fields must not have leading or trailing ASCII spaces',
             'routing fields must not have leading or trailing ASCII spaces'),
            ('IP-CIDR,192.0.2.0/24,DIRECT,no-resolve',
             'Dewu domain-only model cannot validate preceding IP conditions',
             'Dewu domain-only model cannot validate preceding IP conditions'),
        ):
            with self.subTest(rule=row):
                self.write(path, original.replace(MARKER, '  - ' + row + '\n' + MARKER))
                self.rejected(reason, tree_reason)

    def test_mismatched_local_registration_fails_direct_guard(self):
        path = 'local-rulesets.json'
        original = json.loads(self.read(path))
        original['Dewu']['path'] = 'ruleset/Weibo.yaml'
        self.write(path, json.dumps(original, ensure_ascii=False))
        self.rejected('Dewu is missing its dedicated local classical provider', 'ruleset file mismatch')

    def test_non_security_preemption_including_ascii_case(self):
        path = 'config/rules.yaml'
        original = self.read(path)
        variants = ('DOMAIN,dewu.com,DIRECT', 'DOMAIN,WWW.DEWU.COM,DIRECT',
                    'DOMAIN-SUFFIX,DEWU.COM,DIRECT', 'DOMAIN-KEYWORD,DEWU,DIRECT')
        for entry in variants:
            with self.subTest(entry=entry):
                self.write(path, original.replace(MARKER, '  - ' + entry + '\n' + MARKER))
                self.rejected('Dewu is shadowed by an earlier rule', 'Dewu is shadowed by an earlier rule')

    def test_security_payload_updates_still_pass(self):
        original_lock = self.read('sources.lock.json')
        for provider in ('Privacy', 'Hijacking'):
            path = f'ruleset/{provider}_No_Resolve.yaml'
            original = self.read(path)
            with self.subTest(provider=provider), contextlib.redirect_stdout(io.StringIO()):
                self.write(path, original + '  - DOMAIN,dewu.com\n  - DOMAIN,WWW.DEWU.COM\n')
                data = (self.root / path).read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                lock = json.loads(original_lock)
                lock['rulesets'][provider].update(bytes=len(data), sha256=digest, upstream_sha256=digest)
                self.write('sources.lock.json', json.dumps(lock, ensure_ascii=False))
                generate(self.root, write=True)
                validate.validate_dewu(self.root)
                self.validate_tree()
                self.write(path, original)
                self.write('sources.lock.json', original_lock)
                generate(self.root, write=True)

    def test_unrelated_unicode_inline_domain_remains_valid(self):
        path = 'config/rules.yaml'
        original = self.read(path)
        self.assertEqual(original.count(MARKER), 1)
        self.write(path, original.replace(MARKER, '  - DOMAIN,WWW.D\u0130D\u0130GLOBAL.COM,DIRECT\n' + MARKER))
        validate.validate_dewu(self.root)
        self.validate_tree()

    def test_unrelated_unicode_keyword_in_valid_mirror_update(self):
        path = 'ruleset/Privacy_No_Resolve.yaml'
        self.write(path, self.read(path) + '  - DOMAIN-KEYWORD,广告示例\n')
        data = (self.root / path).read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        lock = json.loads(self.read('sources.lock.json'))
        lock['rulesets']['Privacy'].update(bytes=len(data), sha256=digest, upstream_sha256=digest)
        self.write('sources.lock.json', json.dumps(lock, ensure_ascii=False))
        with contextlib.redirect_stdout(io.StringIO()):
            generate(self.root, write=True)
            validate.validate_dewu(self.root)
            self.validate_tree()


if __name__ == '__main__':
    unittest.main()
