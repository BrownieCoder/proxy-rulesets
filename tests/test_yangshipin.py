"""Yangshipin exact public entry regressions."""

import public_app_contract as contract

from validate import validate_yangshipin


class YangshipinContract(contract.PublicAppContract):
    hosts = ("www.yangshipin.cn",)
    provider = "Yangshipin"
    target = "🎞️ 央视频"
    controls = (
        "yangshipin.cn", "m.yangshipin.cn", "passport.yangshipin.cn",
        "www.cctv.com", "tv.cctv.com", "news.cctv.com",
        "www.cctv.cn", "www.bilibili.com", "example.org",
    )
    gate = staticmethod(validate_yangshipin)
