"""China Mobile exact public entry regressions."""

import public_app_contract as contract

from validate import validate_china_mobile


class ChinaMobileContract(contract.PublicAppContract):
    hosts = ("wap.10086.cn",)
    provider = "ChinaMobile"
    target = "📱 中国移动"
    controls = (
        "10086.cn", "www.10086.cn", "shop.10086.cn",
        "login.10086.cn", "h.app.coc.10086.cn", "app.10086.cn",
        "mail.10086.cn", "www.10010.com", "www.189.cn",
    )
    gate = staticmethod(validate_china_mobile)
