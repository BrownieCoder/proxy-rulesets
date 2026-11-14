"""Baidu Netdisk production-validator mutations using only public fixtures."""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import validate


class BaiduPanValidator(unittest.TestCase):
    MARKER = '  - RULE-SET,BaiduPan,☁️ 百度网盘\n'

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for directory in ('config', 'ruleset'):
            shutil.copytree(ROOT / directory, self.root / directory)
        for name in ('sources.json', 'local-rulesets.json', 'sources.lock.json'):
            shutil.copyfile(ROOT / name, self.root / name)

    def mutate(self, name, old, new):
        path = self.root / name
        path.write_text(path.read_text().replace(old, new))

    def test_current_contract(self):
        validate.validate_baidu_pan(self.root)

    def test_scope_broadening_is_rejected_by_tree_validation(self):
        self.mutate('ruleset/BaiduPan.yaml', 'DOMAIN,pan.baidu.com', 'DOMAIN-SUFFIX,baidu.com')
        with self.assertRaisesRegex(ValueError, 'two reviewed exact hosts'):
            validate.validate_tree(self.root)

    def test_duplicate_host_is_rejected(self):
        path = self.root / 'ruleset/BaiduPan.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,pan.baidu.com\n')
        with self.assertRaisesRegex(ValueError, 'without duplicates'):
            validate.validate_baidu_pan(self.root)

    def test_late_rule_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', '  - MATCH,', self.MARKER + '  - MATCH,')
        with self.assertRaisesRegex(ValueError, 'broader providers'):
            validate.validate_baidu_pan(self.root)

    def test_bypassing_security_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        self.mutate('config/rules.yaml', 'rules:\n', 'rules:\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'must precede BaiduPan'):
            validate.validate_baidu_pan(self.root)

    def test_preempting_xiaohongshu_order_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '')
        before = '  - RULE-SET,Xiaohongshu,📕 小红书 / REDnote\n'
        self.mutate('config/rules.yaml', before, self.MARKER + before)
        with self.assertRaisesRegex(ValueError, 'must precede BaiduPan'):
            validate.validate_baidu_pan(self.root)

    def test_unknown_top_level_rule_is_rejected(self):
        self.mutate('config/rules.yaml', self.MARKER, '  - DST-PORT,443,DIRECT\n' + self.MARKER)
        with self.assertRaisesRegex(ValueError, 'Unsupported top-level'):
            validate.validate_baidu_pan(self.root)

    def test_proxy_default_is_rejected(self):
        self.mutate('config/proxy-groups.yaml',
                    'name: "☁️ 百度网盘"\n    type: select\n    proxies:\n      - DIRECT',
                    'name: "☁️ 百度网盘"\n    type: select\n    proxies:\n      - "🚀 节点选择"')
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_baidu_pan(self.root)

    def test_group_type_is_checked(self):
        self.mutate('config/proxy-groups.yaml', 'name: "☁️ 百度网盘"\n    type: select',
                    'name: "☁️ 百度网盘"\n    type: fallback')
        with self.assertRaisesRegex(ValueError, 'DIRECT-first select'):
            validate.validate_baidu_pan(self.root)

    def test_legal_security_updates_pass_the_real_validator(self):
        for provider in ('Privacy', 'Hijacking'):
            for kind in ('DOMAIN', 'DOMAIN-SUFFIX'):
                with self.subTest(provider=provider, kind=kind):
                    path = self.root / f'ruleset/{provider}_No_Resolve.yaml'
                    original = path.read_text()
                    path.write_text(original + f'  - {kind},pan.baidu.com\n')
                    try:
                        validate.validate_baidu_pan(self.root)
                    finally:
                        path.write_text(original)

    def test_non_security_preemption_is_rejected(self):
        path = self.root / 'ruleset/ChinaGaming.yaml'
        path.write_text(path.read_text() + '  - DOMAIN,pan.baidu.com\n')
        with self.assertRaisesRegex(ValueError, 'shadowed'):
            validate.validate_baidu_pan(self.root)

    def test_wrong_security_target_is_rejected(self):
        self.mutate('config/rules.yaml', 'RULE-SET,Privacy,REJECT', 'RULE-SET,Privacy,DIRECT')
        with self.assertRaisesRegex(ValueError, 'requires one active rule'):
            validate.validate_baidu_pan(self.root)

    def test_comment_cannot_replace_active_reference(self):
        self.mutate('config/rules.yaml', self.MARKER, self.MARKER.replace('  - ', '  # '))
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_baidu_pan(self.root)

    def test_duplicate_provider_reference_is_rejected(self):
        path = self.root / 'config/rules.yaml'
        path.write_text(path.read_text() + '  - RULE-SET,BaiduPan,DIRECT\n')
        with self.assertRaisesRegex(ValueError, 'exactly one dedicated'):
            validate.validate_baidu_pan(self.root)


if __name__ == "__main__":
    unittest.main()
