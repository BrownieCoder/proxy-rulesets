"""China Telecom exact public entry regressions."""

import public_app_contract as contract

from validate import validate_china_telecom


class ChinaTelecomContract(contract.PublicAppContract):
    hosts = ("www.189.cn",)
    provider = "ChinaTelecom"
    target = "📱 中国电信"
    controls = (
        "189.cn", "gd.189.cn", "m.gd.189.cn",
        "sh.189.cn", "manyou.189.cn", "www.chinatelecom.com.cn",
        "www.10086.cn", "www.10010.com", "www.95598.cn",
        "chinatelecomtsdj.bestpay.com.cn",
    )
    gate = staticmethod(validate_china_telecom)
