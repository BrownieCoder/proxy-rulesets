# Proxy Rulesets

[English](README.md) | [简体中文](README.zh-CN.md)

A self-maintained Clash/Mihomo ruleset mirror with an audited routing layer for mainland China gaming traffic.

The repository stores validated snapshots instead of relying only on upstream URLs. It also separates mainland game services from international game services so a proxy configuration can keep mainland traffic on `DIRECT` while sending international traffic to a US or other proxy node.

## Highlights

- 24 mirrored and checksum-locked upstream rulesets
- 3 locally maintained rulesets, including `ChinaGaming` and `InternationalGaming`
- 93 high-priority mainland game rules
- 25 international-game safeguards
- Atomic synchronization: existing snapshots stay untouched unless every download validates
- Daily GitHub Actions updates
- Offline validation of files, checksums, provider references, duplicates, and routing priority
- Evidence-backed audit covering Tencent/WeGame/Delta Force, NetEase, miHoYo, Perfect World, Seasun, Lilith, Nuverse, Kuro, Hypergryph, PaperGames, Bilibili Games, TapTap, 4399, and others

## Routing model

```text
security/reject rules
        ↓
known international games → final proxy / US node
        ↓
mainland China games      → DIRECT
        ↓
other service rules
        ↓
known international media
        ↓
GEOIP CN                  → DIRECT
        ↓
ChinaMax / LAN / final
```

Mihomo uses first-match routing, so order is part of the design. Keep `InternationalGaming` before `ChinaGaming`, and keep both before broader providers such as Bilibili, Steam, GlobalMedia, and ChinaMax.

The exact host `fastcdn.hoyoverse.com` is intentionally set to `DIRECT` before the broader HoYoverse international rule because it is used by a mainland miHoYo page.

## Quick start

Use the remote provider template after publishing this repository:

1. Merge the `rule-providers` mapping from [`config/rule-providers.remote.yaml`](config/rule-providers.remote.yaml) into your Mihomo configuration.
2. Merge the ordered rules from [`config/rules.yaml`](config/rules.yaml).
3. Replace policy names such as `🧭 Final`, `🕹️ Steam`, and `🇨🇳 China-Global` with policy groups that exist in your configuration.
4. Run `mihomo -t -f your-config.yaml` before activating the configuration.

For a same-directory checkout, use [`config/rule-providers.local.yaml`](config/rule-providers.local.yaml).

## Mainland gaming safeguards

[`ruleset/ChinaGaming.yaml`](ruleset/ChinaGaming.yaml) prioritizes mainland game websites, authentication, launchers, updates, and verified CDN endpoints.

[`ruleset/InternationalGaming.yaml`](ruleset/InternationalGaming.yaml) protects international services that broad China lists may otherwise classify as domestic, including HoYoverse international domains and selected global publishing/SDK endpoints.

The configuration includes `GEOIP,CN,DIRECT,no-resolve` after GlobalMedia and before ChinaMax. This catches raw-IP/UDP mainland game servers without triggering additional DNS resolution or overriding known international-media rules.

Steam is intentionally narrower: verified mainland Steam/Valve download endpoints are in `ChinaGaming`, while the upstream `SteamCN` provider remains on the Steam policy because it also contains broad global suffixes such as `steamcontent.com`.

See the full audit in [English](research/ChinaGaming-audit.en.md) or [Chinese](research/ChinaGaming-audit.md).

## Repository layout

- `ruleset/` — committed ruleset snapshots
- `sources.json` — mirrored upstream URLs and destination paths
- `sources.lock.json` — synchronization metadata and SHA-256 checksums
- `local-rulesets.json` — locally maintained rulesets
- `scripts/sync.py` — atomic downloader, normalizer, and provider generator
- `scripts/validate.py` — offline integrity and configuration validation
- `config/` — local and remote provider templates plus ordered example rules
- `research/` — fact-traceable routing audit

## Updating

```bash
python3 scripts/sync.py
python3 scripts/validate.py
python3 scripts/public_check.py
git diff --stat
```

The sync process downloads and validates every mirrored source before replacing any committed snapshot. A failure leaves the last known-good files intact.

GitHub Actions checks upstream sources daily and commits only material changes. Enable **Settings → Actions → General → Workflow permissions → Read and write permissions** after publishing.

## Accuracy and limitations

Routing data changes. Game clients may connect through raw IPs, shared cloud infrastructure, dynamic UDP endpoints, or hostnames delivered only at runtime. The rules cover verified public endpoints and include a mainland GeoIP fallback, but they cannot guarantee every game session or region.

For high-confidence additions, capture DNS/SNI/connection logs during a mainland client flow—cold start, login, update, and one match—and submit evidence with the proposed rule.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). New rules should identify the mainland or international boundary, include authoritative evidence, and explain the risk of matching a shared root domain.

## License and third-party material

Project-authored code, documentation, and locally maintained rules are released under the [GNU General Public License v2.0](LICENSE).

Mirrored files remain attributable to their respective upstream authors and may carry additional notices or source-specific terms. Review [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and `sources.json` before redistribution. This project is not affiliated with Mihomo, Clash, any game publisher, or any upstream ruleset project.

Provided without warranty. You are responsible for checking local law, upstream terms, and routing behavior before use.
