"""Vipshop exact public entry regressions."""

import json

import yaml

import public_app_contract as contract

import validate
from generate_catalog import generate, read_rules
from validate import validate_vipshop


class VipshopContract(contract.PublicAppContract):
    hosts = ("www.vip.com",)
    provider = "Vipshop"
    target = "🛍️ 唯品会"
    controls = (
        "vip.com", "m.vip.com", "help.vip.com",
        "myi.vip.com", "vis.vip.com", "www.vipshop.com",
        "www.vpal.com", "a.vpimg2.com", "mst.vip.com",
    )
    gate = staticmethod(validate_vipshop)

    def _privacy_fixture(self, *additional):
        path = json.loads(self.read("sources.json"))["Privacy"]["path"]
        entries = [rule for rule in read_rules(self.read(path))
                   if not contract._domain_model([rule]).matches(self.hosts[0])]
        entries.extend(additional)
        text = yaml.safe_dump({"payload": entries}, allow_unicode=True)
        self._write_fixture_mirror("Privacy", path, text)
        self.assertEqual(read_rules(text), entries)
        generate(self.root, write=True)
        self.gate(self.root)
        return path, text, entries

    def test_privacy_fixture_removal_preserves_quoted_keyword(self):
        path, text, entries = self._privacy_fixture("DOMAIN,www.vip.com", "DOMAIN-KEYWORD,review-example:")
        self.assertIn("'DOMAIN-KEYWORD,review-example:'", text)

        self._clear_fixture_security_matches()

        kept = [rule for rule in entries if rule != "DOMAIN,www.vip.com"]
        self.assertEqual(read_rules(self.read(path)), kept)
        self.assertEqual(yaml.safe_load(self.read(path)), {"payload": kept})
        self.assertEqual(validate.validate_tree(self.root), 0)

    def test_privacy_fixture_append_accepts_unindented_payload(self):
        path, text, _ = self._privacy_fixture("DOMAIN,unrelated.example.org")
        self.assertIn("\n- DOMAIN,unrelated.example.org\n", text)

        self._assert_legal_security_precedence_holds()

        self.assertEqual(self.read(path), text)
