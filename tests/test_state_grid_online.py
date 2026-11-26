"""State Grid Online exact public entry regressions."""

import public_app_contract as contract

from validate import validate_state_grid_online


class StateGridOnlineContract(contract.PublicAppContract):
    hosts = ("www.95598.cn",)
    provider = "StateGridOnline"
    target = "⚡ 网上国网"
    controls = (
        "95598.cn", "sgcc.com.cn", "www.sgcc.com.cn",
        "csc-static.sgcc.com.cn", "www.189.cn", "www.10086.cn",
        "www.10010.com", "guzzoni.apple.com", "example.org",
    )
    gate = staticmethod(validate_state_grid_online)
