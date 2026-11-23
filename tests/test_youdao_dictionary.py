"""Youdao Dictionary exact public entry regressions."""

import public_app_contract as contract

from validate import validate_youdao_dictionary


class YoudaoDictionaryContract(contract.PublicAppContract):
    hosts = ("dict.youdao.com",)
    provider = "YoudaoDictionary"
    target = "📖 网易有道词典"
    controls = (
        "youdao.com", "www.youdao.com", "fanyi.youdao.com",
        "cidian.youdao.com", "account.youdao.com", "ke.youdao.com",
        "note.youdao.com", "ydlunacommon.nosdn.127.net", "rlogs.youdao.com",
        "mail.163.com",
    )
    gate = staticmethod(validate_youdao_dictionary)
