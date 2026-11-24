"""Pupu Mall exact public entry regressions."""

import public_app_contract as contract

from validate import validate_pupu_mall


class PupuMallContract(contract.PublicAppContract):
    hosts = ("www.pupumall.com",)
    provider = "PupuMall"
    target = "🛒 朴朴超市"
    controls = (
        "pupumall.com", "pupumall.net", "www.pupumall.net",
        "c.pupuapi.com", "ma.pupumall.com", "www.100.me",
        "maicai.api.ddxq.mobi", "www.freshippo.com",
    )
    gate = staticmethod(validate_pupu_mall)
