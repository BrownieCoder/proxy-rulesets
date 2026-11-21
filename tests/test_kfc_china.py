"""KFC China exact public entry regressions."""

import public_app_contract as contract

from validate import validate_kfc_china


class KFCChinaContract(contract.PublicAppContract):
    hosts = ("www.kfc.com.cn",)
    provider = "KFCChina"
    target = "🍗 肯德基中国"
    controls = (
        "kfc.com.cn", "www.kfc.com", "www.yumchina.com",
        "www.4008823823.com.cn", "www.mcdonalds.com.cn", "appcommon.kfc.com.cn",
    )
    gate = staticmethod(validate_kfc_china)
