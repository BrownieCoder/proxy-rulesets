"""Dingdong Maicai exact public entry regressions."""

import json

import public_app_contract as contract

from generate_catalog import generate, read_rules
from validate import validate_tree
from validate import validate_dingdong_maicai


class DingdongMaicaiContract(contract.PublicAppContract):
    hosts = ("www.100.me",)
    provider = "DingdongMaicai"
    target = "🥬 叮咚买菜"
    controls = ("100.me", "maicai.api.ddxq.mobi", "www.freshippo.com", "www.pupumall.com",)
    gate = staticmethod(validate_dingdong_maicai)

    def test_chinamax_can_drop_the_entry_without_changing_its_app_route(self):
        self._clear_fixture_security_matches()
        host, = self.hosts
        path = json.loads(self.read("sources.json"))["ChinaMax"]["path"]
        rules = read_rules(self.read(path))
        remaining = [rule for rule in rules if not contract._domain_model([rule]).matches(host)]
        if remaining != rules:
            payload = "payload:\n" + "".join(f"  - {rule}\n" for rule in remaining)
            self._write_fixture_mirror("ChinaMax", path, payload)
            generate(self.root, write=True)
        ordered, models = self._current_model()
        self.assertFalse(models["ChinaMax"].matches(host))
        self.assertEqual(self._route(host, ordered, models), (self.provider, self.target))
        self.assertNotEqual(self._route(host, ordered, models, skip_app=True)[0], "ChinaMax")
        self.assertEqual(validate_tree(self.root), 0)
