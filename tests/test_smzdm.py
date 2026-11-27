"""SMZDM exact public entry regressions."""

import public_app_contract as contract

from validate import validate_smzdm


class SMZDMContract(contract.PublicAppContract):
    hosts = ("www.smzdm.com",)
    provider = "SMZDM"
    target = "🏷️ 什么值得买"
    controls = (
        "smzdm.com", "post.smzdm.com", "zhiyou.smzdm.com",
        "zhiyou.m.smzdm.com", "res.smzdm.com", "static.smzdm.com",
        "qny.smzdm.com", "y.zdmimg.com", "e.smzdm.com",
    )
    gate = staticmethod(validate_smzdm)
