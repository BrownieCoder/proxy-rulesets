# Proxy Rulesets

Public rules for AI, Apple, gaming, media and network services. **Choose a service, then choose your client.**

[Service directory (Chinese)](README.md#选择服务) · [Client guidance](docs/clients/mihomo.md) · [Maintainer guide](docs/maintainer/README.md)

The static install center is prepared in `install/index.html`, but is not publicly hosted yet. Existing raw rule URLs are available through the directory. They are Mihomo rule files, not node subscriptions or complete profiles.

Shadowrocket: only the fixed REJECT Privacy module can preserve the repository's existing policy and precedence. It has been generated locally but is not published yet. Modules do not replace nodes or the main configuration, but their rules take priority. Other services require manual setup; flattening selectable policies to PROXY would change routing.

ClashX.Meta imports complete configurations, switches to them, and may replace a same-named remote configuration. Clash Verge Rev and Clash Party normally add a complete profile and may enable it if none is selected. None of these schemes merges a standalone rule provider into the current profile. Use the linked client guidance; do not paste a provider URL into a subscription import field.

Siri AI rules only select a network route. They do not change hardware, account, region or language eligibility, and include ordinary Siri/dictation endpoints.

No nodes, subscriptions, credentials, MITM, analytics or new permissions are included. Preserve security rules first, international gaming before China gaming, and service rules before broader matches. See the [advanced guide](docs/advanced.md) for the complete ordered contract.

Project-authored material is licensed under [GPL-2.0](LICENSE). Mirrored and derived rules retain their upstream attribution and terms in [third-party notices](THIRD_PARTY_NOTICES.md). Client evidence is documented with versions in the [capability research](docs/maintainer/client-capabilities.md).
