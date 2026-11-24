"""Cainiao exact public entry regressions."""

import public_app_contract as contract

from validate import validate_cainiao


class CainiaoContract(contract.PublicAppContract):
    hosts = ("newconnection.cainiao.com",)
    provider = "Cainiao"
    target = "📦 菜鸟"
    controls = (
        "cainiao.com", "www.cainiao.com", "page.cainiao.com",
        "img.alicdn.com", "cainiaoyizhan.com", "www.cainiao.com.cn",
        "www.taobao.com", "www.sf-express.com", "www.zto.com",
    )
    gate = staticmethod(validate_cainiao)
