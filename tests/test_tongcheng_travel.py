"""Tongcheng Travel exact public entry regressions."""

import public_app_contract as contract

from validate import validate_tongcheng_travel


class TongchengTravelContract(contract.PublicAppContract):
    hosts = ("m.ly.com",)
    provider = "TongchengTravel"
    target = "🧳 同程旅行"
    controls = ("ly.com", "www.ly.com", "m.17u.cn", "tmc.ly.com", "passport.ly.com", "pic5.40017.cn", "www.12306.cn", "m.ctrip.com",)
    gate = staticmethod(validate_tongcheng_travel)
