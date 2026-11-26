"""Dongchedi exact public entry regressions."""

import public_app_contract as contract

from validate import validate_dongchedi


class DongchediContract(contract.PublicAppContract):
    hosts = ("www.dongchedi.com",)
    provider = "Dongchedi"
    target = "🚘 懂车帝"
    controls = (
        "dongchedi.com", "m.dongchedi.com", "dcdapp.com",
        "dongchediapp.com", "lf3-cdn-tos.draftstatic.com", "api.dcarapi.com",
        "www.autohome.com.cn", "www.yiche.com", "www.douyin.com",
        "example.org",
    )
    gate = staticmethod(validate_dongchedi)
