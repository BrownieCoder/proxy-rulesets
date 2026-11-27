"""Autohome exact public entry regressions."""

import public_app_contract as contract

from validate import validate_autohome


class AutohomeContract(contract.PublicAppContract):
    hosts = ("www.autohome.com.cn",)
    provider = "Autohome"
    target = "🚗 汽车之家"
    controls = (
        "autohome.com.cn", "m.autohome.com.cn", "www.athmapp.com",
        "account.autohome.com.cn", "comm.app.autohome.com.cn", "sou.api.autohome.com.cn",
        "z.autoimg.cn", "al.autohome.com.cn", "live.autohome.com.cn",
        "www.dongchedi.com", "www.yiche.com", "www.che168.com",
    )
    gate = staticmethod(validate_autohome)
