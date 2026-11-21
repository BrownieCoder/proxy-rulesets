"""DouYu exact public entry regressions."""

import public_app_contract as contract

from validate import validate_douyu


class DouYuContract(contract.PublicAppContract):
    hosts = ("m.douyu.com",)
    provider = "DouYu"
    target = "🐟 斗鱼"
    controls = ("douyu.com", "www.douyu.com", "v.douyu.com", "wan.douyu.com", "staticlive.douyucdn.cn",)
    gate = staticmethod(validate_douyu)
