"""Tencent Docs exact public entry regressions."""

import public_app_contract as contract

from validate import validate_tencent_docs


class TencentDocsContract(contract.PublicAppContract):
    hosts = ("docs.qq.com",)
    provider = "TencentDocs"
    target = "📝 腾讯文档"
    controls = ("qq.com", "im.qq.com", "meeting.tencent.com", "work.weixin.qq.com", "beacon.qq.com", "weread.qq.com", "gtimg.com",)
    gate = staticmethod(validate_tencent_docs)
