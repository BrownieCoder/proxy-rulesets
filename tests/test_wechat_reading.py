"""Public-entry first-match and full-tree regressions for WeRead."""

import public_app_contract as contract

from validate import validate_wechat_reading


class WeChatReadingContract(contract.PublicAppContract):
    hosts = ("weread.qq.com",)
    provider = "WeChatReading"
    target = "📚 微信读书"
    controls = (
        "example.org", "fastcdn.hoyoverse.com", "guzzoni.apple.com",
        "hmma.baidu.com", "hoyoverse.com", "im.qq.com", "mp.weixin.qq.com",
        "myqcloud.com", "qq.com", "v.qq.com", "weixin.qq.com",
        "www.bilibili.com", "www.douyin.com", "www.google.com", "www.taobao.com",
        "www.youku.com", "y.qq.com", "yuedu.qq.com",
    )
    gate = staticmethod(validate_wechat_reading)
