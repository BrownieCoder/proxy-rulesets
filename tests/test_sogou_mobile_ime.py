"""Sogou Mobile IME exact public entry regressions."""

import public_app_contract as contract

from validate import validate_sogou_mobile_ime


class SogouMobileIMEContract(contract.PublicAppContract):
    hosts = ("shouji.sogou.com",)
    provider = "SogouMobileIME"
    target = "⌨️ 搜狗输入法手机版"
    controls = (
        "sogou.com", "pinyin.sogou.com", "shurufa.sogou.com",
        "account.sogou.com", "indivi-cdn.shouji.sogou.com", "img.shouji.sogou.com",
        "apkdl.sogouimecdn.com", "pb.i.sogou.com",
    )
    gate = staticmethod(validate_sogou_mobile_ime)
