"""Xigua Video exact public entry regressions."""

import public_app_contract as contract

from validate import validate_xigua_video


class XiguaVideoContract(contract.PublicAppContract):
    hosts = ("m.ixigua.com",)
    provider = "XiguaVideo"
    target = "🍉 西瓜视频"
    controls = (
        "ixigua.com", "www.ixigua.com", "studio.ixigua.com",
        "live.ixigua.com", "p3.bdxiguaimg.com", "www.douyin.com",
        "reading.snssdk.com",
    )
    gate = staticmethod(validate_xigua_video)
