"""Fanqie Novel exact public entry regressions."""

import public_app_contract as contract

from validate import validate_fanqie_novel


class FanqieNovelContract(contract.PublicAppContract):
    hosts = ("fanqienovel.com",)
    provider = "FanqieNovel"
    target = "🍅 番茄小说"
    controls = (
        "www.fanqienovel.com", "www.changdunovel.com", "reading.snssdk.com",
        "lf-organic-growth.bytecdn.cn", "www.douyin.com",
    )
    gate = staticmethod(validate_fanqie_novel)
