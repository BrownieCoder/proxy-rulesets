"""Ximalaya exact public entry regressions."""

import public_app_contract as contract

from validate import validate_ximalaya


class XimalayaContract(contract.PublicAppContract):
    hosts = ("m.ximalaya.com",)
    provider = "Ximalaya"
    target = "🎧 喜马拉雅"
    controls = (
        "ximalaya.com", "www.ximalaya.com", "passport.ximalaya.com",
        "live.ximalaya.com", "studio.ximalaya.com", "open.ximalaya.com",
        "everest-ai.ximalaya.com",
    )
    gate = staticmethod(validate_ximalaya)
