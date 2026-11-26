"""China University MOOC exact public entry regressions."""

import public_app_contract as contract

from validate import validate_china_university_mooc


class ChinaUniversityMOOCContract(contract.PublicAppContract):
    hosts = ("www.icourse163.org",)
    provider = "ChinaUniversityMOOC"
    target = "🎓 中国大学 MOOC"
    controls = (
        "icourse163.org", "m.icourse163.org", "corp.163.com",
        "study.163.com", "higher.smartedu.cn", "mooc-image.nosdn.127.net",
        "dict.youdao.com", "music.163.com", "example.org",
    )
    gate = staticmethod(validate_china_university_mooc)
