"""Keep Fitness exact public entry regressions."""

import public_app_contract as contract

from validate import validate_keep_fitness


class KeepFitnessContract(contract.PublicAppContract):
    hosts = ("www.calorietech.com",)
    provider = "KeepFitness"
    target = "🏃 Keep"
    controls = (
        "calorietech.com", "gotokeep.com", "www.gotokeep.com",
        "show.gotokeep.com", "m.gotokeep.com", "mo.gotokeep.com",
        "static1.keepcdn.com", "staticweb.keepcdn.com", "keep.com",
        "ir.keep.com",
    )
    gate = staticmethod(validate_keep_fitness)
