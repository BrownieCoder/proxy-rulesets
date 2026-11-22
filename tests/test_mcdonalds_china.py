"""McDonald’s China exact public entry regressions."""

import public_app_contract as contract

from validate import validate_mcdonalds_china


class McDonaldsChinaContract(contract.PublicAppContract):
    hosts = ("www.mcdonalds.com.cn",)
    provider = "McDonaldsChina"
    target = "🍔 麦当劳中国"
    controls = (
        "mcdonalds.com.cn", "www.mcdonalds.com", "www.mcd.cn",
        "www.4008-517-517.cn", "www.kfc.com.cn",
    )
    gate = staticmethod(validate_mcdonalds_china)
