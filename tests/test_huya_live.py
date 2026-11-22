"""Huya Live exact public entry regressions."""

import public_app_contract as contract

from validate import validate_huya_live


class HuyaLiveContract(contract.PublicAppContract):
    hosts = ("hd.huya.com",)
    provider = "HuyaLive"
    target = "🐯 虎牙直播"
    controls = (
        "huya.com", "www.huya.com", "m.huya.com",
        "api.m.huya.com", "app-agreements.huya.com", "dev.huya.com",
        "rel.huya.com", "metric.huya.com",
    )
    gate = staticmethod(validate_huya_live)
