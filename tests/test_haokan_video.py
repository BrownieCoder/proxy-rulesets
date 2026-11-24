"""Haokan Video exact public entry regressions."""

import public_app_contract as contract

from validate import validate_haokan_video


class HaokanVideoContract(contract.PublicAppContract):
    hosts = ("haokan.baidu.com",)
    provider = "HaokanVideo"
    target = "🎬 好看视频"
    controls = (
        "baidu.com", "www.baidu.com", "m.baidu.com",
        "map.baidu.com", "passport.baidu.com", "baijiahao.baidu.com",
        "imgsa.baidu.com", "mobile.baidu.com", "image.baidu.com",
        "mpics.bdstatic.com", "live.baidu.com",
    )
    gate = staticmethod(validate_haokan_video)
