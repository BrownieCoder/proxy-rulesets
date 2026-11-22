"""Vipshop exact public entry regressions."""

import public_app_contract as contract

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
