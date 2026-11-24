"""China Unicom exact public entry regressions."""

import public_app_contract as contract

from validate import validate_china_unicom


class ChinaUnicomContract(contract.PublicAppContract):
    hosts = ("wap.10010.com",)
    provider = "ChinaUnicom"
    target = "📶 中国联通"
    controls = (
        "10010.com", "www.10010.com", "m.10010.com",
        "mall.10010.com", "m.client.10010.com", "uac.10010.com",
        "img.client.10010.com", "res.mall.10010.cn", "www.chinaunicom.com",
        "wap.10086.cn", "www.189.cn", "m1.img.10010.com",
    )
    gate = staticmethod(validate_china_unicom)
