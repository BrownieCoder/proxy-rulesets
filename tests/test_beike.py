"""Beike exact public entry regressions."""

import public_app_contract as contract

from validate import validate_beike


class BeikeContract(contract.PublicAppContract):
    hosts = ("www.ke.com",)
    provider = "Beike"
    target = "🏠 贝壳找房"
    controls = (
        "ke.com", "bj.ke.com", "sh.ke.com",
        "m.ke.com", "wap.ke.com", "map.ke.com",
        "ajax.api.ke.com", "file.ljcdn.com", "img.ljcdn.com",
        "bkzhibo.com", "www.lianjia.com", "www.anjuke.com",
        "www.fang.com",
    )
    gate = staticmethod(validate_beike)
