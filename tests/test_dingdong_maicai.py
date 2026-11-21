"""Dingdong Maicai exact public entry regressions."""

import public_app_contract as contract

from validate import validate_dingdong_maicai


class DingdongMaicaiContract(contract.PublicAppContract):
    hosts = ("www.100.me",)
    provider = "DingdongMaicai"
    target = "🥬 叮咚买菜"
    controls = ("100.me", "maicai.api.ddxq.mobi", "www.freshippo.com", "www.pupumall.com",)
    gate = staticmethod(validate_dingdong_maicai)
