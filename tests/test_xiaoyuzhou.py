"""Xiaoyuzhou exact public entry regressions."""

import public_app_contract as contract

from validate import validate_xiaoyuzhou


class XiaoYuZhouContract(contract.PublicAppContract):
    hosts = ("www.xiaoyuzhoufm.com",)
    provider = "XiaoYuZhou"
    target = "🎙️ 小宇宙"
    controls = (
        "xiaoyuzhoufm.com", "blog.xiaoyuzhoufm.com", "studio.xiaoyuzhoufm.com",
        "static.xiaoyuzhoufm.com", "post.xiaoyuzhoufm.com", "image.xyzcdn.net",
        "post.jellow.club", "m.ximalaya.com", "www.lizhi.fm",
        "accounts.xiaoyuzhoufm.com",
    )
    gate = staticmethod(validate_xiaoyuzhou)
