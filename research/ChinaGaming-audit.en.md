# ChinaGaming Deep Audit

[English](ChinaGaming-audit.en.md) | [简体中文](ChinaGaming-audit.md)

Audit date: 2026-07-26

## Goal and outcome

The goal is to send verified mainland China game websites, authentication, launchers, updates, and identifiable CDN traffic through `DIRECT`, while keeping international game services on the final US/proxy route.

The resulting model has three layers:

1. `InternationalGaming → final proxy`: protect known international services first.
2. `ChinaGaming → DIRECT`: match mainland game services.
3. `GEOIP,CN → DIRECT`: cover raw-IP and UDP endpoints located in mainland China.

One exact-host exception precedes these providers: `fastcdn.hoyoverse.com` is used by a mainland miHoYo page, so it is routed directly before the broader international `hoyoverse.com` suffix.

The upstream `SteamCN` provider mixes verified mainland download nodes with global suffixes such as `steamcontent.com`, `steamserver.net`, and `steamusercontent.com`. Routing the entire provider directly would also capture global Steam content. This repository extracts verified mainland nodes into `ChinaGaming` and leaves the broad upstream provider on the configured Steam policy.

## Important coverage fact

ChinaMax currently includes:

```yaml
- DOMAIN-SUFFIX,cn
```

Any `.cn` candidate already reaches ChinaMax unless an earlier rule captures it. Listing those domains explicitly in `ChinaGaming` still matters because it:

- places them before GlobalMedia, Bilibili, Steam, and ChinaMax;
- documents the intent that mainland game traffic should be direct;
- preserves them if a future upstream update removes the broad `.cn` suffix.

These `.cn` entries are priority hardening, not previously unmatched ChinaMax coverage. The clearest non-`.cn` gap found during the audit was `lilithcdn.com`. `fastcdn.hoyoverse.com` is a separate exact-host mainland override inside an otherwise international root domain.

## Ten research tracks

1. Tencent, WeGame, and Delta Force
2. NetEase Games
3. Mainland miHoYo versus international HoYoverse
4. Perfect World, Valve China, and Kingsoft/Seasun
5. Nuverse and Lilith Games
6. Kuro Games, Hypergryph, and PaperGames
7. Bilibili Games, Yoozoo, 37 Interactive, and 4399
8. Mainland game platforms, distribution, and CDN infrastructure
9. Authentication, real-name verification, anti-addiction, anti-cheat, voice, and update SDKs
10. Effective first-match review across ChinaMax, SteamCN, Bilibili, and GlobalMedia

## Primary-source evidence

### Tencent and Delta Force

- The [Delta Force mainland website](https://df.qq.com/) uses `df.qq.com`, `repo.df.qq.com`, and `game.gtimg.cn`.
- The [WeGame mainland client page](https://www.wegame.com.cn/client/) and [official agreement](https://www.wegame.com.cn/contract/) establish `wegame.com.cn` as a platform for game downloads, login, and updates.
- [Tencent ACE for PC](https://anticheatexpert.com/products/anti-cheat-pc) is a global service, so no new broad ACE root was added to the mainland-only layer.

### NetEase

- The [NetEase corporate website](https://www.netease.com/) identifies `game.163.com` as the NetEase Games website.
- The [NARAKA mainland FAQ](https://www.yjwujian.cn/news/official/20210330/32319_939599.html) separates the mainland NetEase-account client from Steam/global accounts. Its [download page](https://www.yjwujian.cn/download/) uses NetEase `gdl` distribution hosts.
- [NetEase Games AI Lab](https://aigame.netease.com/) documents anti-cheat technology used across NetEase games.
- `easebar.com` and `narakathegame.com` are associated with international services and were not added to the mainland layer.

### miHoYo

- The mainland sites for [Genshin Impact](https://ys.mihoyo.com/), [Honkai Impact 3](https://bh3.mihoyo.com/main/), [Honkai: Star Rail](https://sr.mihoyo.com/), and [Zenless Zone Zero](https://zzz.mihoyo.com/) establish the mainland `mihoyo.com` and game-specific roots.
- An [official Star Rail installation guide](https://webstatic.mihoyo.com/upload/static-resource/2023/02/09/a323f3886a63e59302e92aee3757e06d_5764665766985374511.pdf) identifies `autopatchcn.bhsr.com`.
- An [official Zenless Zone Zero notice](https://zzz.mihoyo.com/news/162438) uses `mhyurl.cn`.
- `hoyoverse.com`, `hoyolab.com`, `genshinimpact.com`, and other international roots remain on the proxy route; only the exact mainland-referenced `fastcdn.hoyoverse.com` is direct.

### Perfect World, Valve China, and Seasun

- The [Dota 2 mainland download page](https://www.dota2.com.cn/download/) and [CS mainland download page](https://www.csgo.com.cn/download/index.html) establish `dota2.com.cn`, `csgo.com.cn`, `pwesports.cn`, and Steam China flows.
- A [Perfect World game download page](https://world2.wanmei.com/download/index.shtml) uses `wanmei.com` and `arc.arcgames.cn`.
- The [JX3 patch page](https://jx3.xoyo.com/patch/) and [official editor documentation](https://sceneeditor.jx3.xoyo.com/partials/readme.html) establish `xoyo.com` and `xoyocdn.com`.
- The [Mecha BREAK mainland site](https://mechabreak.seasungames.cn/) uses `seasungames.cn`; `seasungames.com` is treated as international.

### Nuverse, Lilith, Kuro, Hypergryph, and PaperGames

- The [Nuverse mainland site](https://www.nvsgames.cn/) and its product API use `nvsgames.cn`; the `.com` site is global.
- The [Lilith website](https://www.lilith.com/index.html) exposes mainland products, accounts, and PC downloads under `lilith.com` and `lilithgame.com`, with official assets on `lilithcdn.com`. The international publishing root `farlightgames.com` is excluded.
- The [Wuthering Waves mainland entry](https://mc.kurogame.com/) and its resources use `kurogame.com`, `kurogames.com`, and `aki-game*`; `kurogames-global.com` is international.
- [Hypergryph customer support](https://customer-service.hypergryph.com/app/endfield/question/ART177649315709249426294301) directly publishes a `launcher.hycdn.cn` updater component. An [Arknights PC notice](https://ak.hypergryph.com/news/7388) confirms launcher-based downloads and updates.
- The [Infinity Nikki mainland privacy page](https://infinitynikki.nuanpaper.com/notice/privacy) and mainland pages use `nuanpaper.com` and `papegames.com`; `infoldgames.com` is treated as an international publishing root.

### Mainland platforms, channels, and compliance

- [TapTap China](https://www.taptap.cn/about-us) and its [login documentation](https://developer.taptap.cn/docs/sdk/taptap-login/taptap-oauth/) explicitly distinguish mainland `open.tapapis.cn` from the overseas `.com` endpoint.
- [TapTap gift documentation](https://developer.taptap.cn/docs/sdk/tds-gift/guide/) uses mainland `poster-api.xd.cn` and overseas `.com`.
- The [9Game download page](https://app.9game.cn/) uses `9game.cn`.
- [vivo App Store/Game Center documentation](https://swsdl.vivo.com.cn/appstore/developer/staticres/4.3/doc/products/pc/index.html) establishes the `vivo.com.cn` download and game-center flow.
- [4399 Game Box documentation](https://www.4399.cn/help/FunctionIntroduce.html) and its [download page](https://app.4399.cn/sem/game/xmtyytfgzh-25.html) establish `4399.cn`.
- The [NPPA anti-addiction API specification](https://wlc.nppa.gov.cn/2022/02/18/a080ffa8a7ff4005b7c3dbbfcce93323.pdf) lists `api.wlc.nppa.gov.cn` and `api2.wlc.nppa.gov.cn`.

## Explicit exclusions and international protection

A root domain should not be forced direct merely because the operator is a Chinese company. The mainland layer deliberately avoids:

- international publishing roots used by HoYoverse, NetEase, Lilith, Kuro, Hypergryph, and PaperGames;
- shared Akamai, AWS, Cloudflare, Alibaba OSS, and Tencent COS roots;
- mixed-use services such as `steamstatic.com`, `qcloud.com`, `myqcloud.com`, and `gmertc.com`;
- third-party analytics and attribution services such as AppsFlyer, Adjust, Google, and Facebook.

`InternationalGaming.yaml` also corrects international domains that broad China lists may otherwise route directly, including international miHoYo domains, `bilibili.tv`, `37games.com`, the overseas TapTap API, and explicit international GME hosts.

## What public web research cannot prove

Live game sessions may use:

- raw IP addresses;
- dynamically assigned UDP endpoints;
- shared cloud-provider infrastructure;
- hostnames delivered only after the client starts.

The current rules cover verified websites, authentication, launchers, patching, and public CDN endpoints. `GEOIP,CN,DIRECT,no-resolve` catches targets recognized as mainland IPs, but runtime capture is still required for endpoints outside current GeoIP data, shared or overseas cloud regions, or hosts that must be separated by game region.

A second-stage audit should capture DNS, SNI, target IPs, and ASNs during a mainland client flow: cold start, login, update, and one live match.
