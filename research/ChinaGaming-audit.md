# ChinaGaming 深度审计

[English](ChinaGaming-audit.en.md) | [简体中文](ChinaGaming-audit.md)

审计日期：2026-07-26

## 目标与结论

目标是让中国大陆游戏的官网、登录、启动器、更新和可识别 CDN 流量优先走 `DIRECT`，同时让国际服继续走最终的美国节点。

最终采用两层规则：

1. `InternationalGaming → 🧭 Final`：先保护已确认的国际服域名。
2. `ChinaGaming → DIRECT`：再匹配大陆游戏服务。
3. `GEOIP,CN → DIRECT`：为直接使用中国大陆 IP 的对局/UDP 节点兜底。

唯一的顺序例外是 `fastcdn.hoyoverse.com`：米哈游国服官网当前使用该精确主机，因此在 `InternationalGaming` 的 `hoyoverse.com` 后缀之前显式设为 `DIRECT`。

上游 `SteamCN` 同时含有明确的中国下载节点，以及宽泛的 `steamcontent.com`、`steamserver.net`、`steamusercontent.com`。直接把整个 provider 改成 `DIRECT` 会连带全球 Steam 内容。本次把可确认的中国节点提取进 `ChinaGaming`，让它们优先直连；原 `SteamCN` 继续沿用 `🕹️ Steam`。

## 重要的覆盖事实

ChinaMax 当前包含：

```yaml
- DOMAIN-SUFFIX,cn
```

因此所有 `.cn` 候选原本就会在未被更早规则命中时进入 ChinaMax。它们加入 `ChinaGaming` 的价值是：

- 提前到 GlobalMedia、Bilibili、Steam 和 ChinaMax 之前；
- 明确表达“国服必须直连”的维护意图；
- 即使未来上游移除宽泛 `.cn`，国服规则仍然存在。

不能把这些 `.cn` 条目称为 ChinaMax 的真实新增覆盖。当前最明确的非 `.cn` 新缺口是 `lilithcdn.com`；`fastcdn.hoyoverse.com` 则是需要从国际根域中精确覆盖的国服资源主机。

## 10 个并行研究方向

1. 腾讯、WeGame 与《三角洲行动》
2. 网易游戏
3. 米哈游国服与 HoYoverse 国际服边界
4. 完美世界、Valve 国服、西山居
5. 朝夕光年与莉莉丝
6. 库洛、鹰角、叠纸
7. Bilibili 游戏、游族、三七、4399
8. 国内游戏平台和游戏分发/CDN
9. 登录、实名、防沉迷、反作弊、语音 SDK
10. ChinaMax/SteamCN/Bilibili/GlobalMedia 实际匹配顺序复核

## 官方证据摘要

### 腾讯与《三角洲行动》

- [《三角洲行动》官网](https://df.qq.com/) 使用 `df.qq.com`、`repo.df.qq.com` 和 `game.gtimg.cn`。
- [WeGame 中国客户端](https://www.wegame.com.cn/client/) 及[官方协议](https://www.wegame.com.cn/contract/)证明 `wegame.com.cn` 用于平台下载、登录和更新。
- [腾讯 ACE PC 反作弊](https://anticheatexpert.com/products/anti-cheat-pc)是全球服务，故没有把新的 ACE 泛域加入专用大陆层。

### 网易

- [网易公司官网](https://www.netease.com/)将 `game.163.com` 列为网易游戏官网。
- [永劫无间国服 FAQ](https://www.yjwujian.cn/news/official/20210330/32319_939599.html)明确国服客户端、网易通行证与 Steam/全球服账号分离；[国服下载页](https://www.yjwujian.cn/download/)使用网易 `gdl` 分发域。
- [网易游戏 AI Lab](https://aigame.netease.com/)说明其反外挂能力被网易游戏使用。
- `easebar.com` 和 `narakathegame.com` 与海外服相关，未放入大陆层。

### 米哈游

- [原神国服](https://ys.mihoyo.com/)、[崩坏 3 国服](https://bh3.mihoyo.com/main/)、[星穹铁道国服](https://sr.mihoyo.com/)和[绝区零国服](https://zzz.mihoyo.com/)证明国服使用 `mihoyo.com` 及各国服游戏根域。
- [星铁官方安装指南](https://webstatic.mihoyo.com/upload/static-resource/2023/02/09/a323f3886a63e59302e92aee3757e06d_5764665766985374511.pdf)明确出现 `autopatchcn.bhsr.com`。
- [绝区零官方公告](https://zzz.mihoyo.com/news/162438)使用 `mhyurl.cn`。
- `hoyoverse.com`、`hoyolab.com`、`genshinimpact.com`、`honkaistarrail.com` 等保留给国际服；只精确覆盖国服页面使用的 `fastcdn.hoyoverse.com`。

### 完美世界、Valve 国服和西山居

- [DOTA2 国服下载](https://www.dota2.com.cn/download/)与[CS 国服下载](https://www.csgo.com.cn/download/index.html)证明 `dota2.com.cn`、`csgo.com.cn`、`pwesports.cn` 和蒸汽平台链路。
- [完美世界端游下载](https://world2.wanmei.com/download/index.shtml)使用 `wanmei.com` 以及 `arc.arcgames.cn`。
- [剑网 3 补丁页](https://jx3.xoyo.com/patch/)与[官方编辑器说明](https://sceneeditor.jx3.xoyo.com/partials/readme.html)证明 `xoyo.com`、`xoyocdn.com`。
- [解限机国服官网](https://mechabreak.seasungames.cn/)使用 `seasungames.cn`；`seasungames.com` 是国际站，因此进入国际层。

### 朝夕光年、莉莉丝、库洛、鹰角、叠纸

- [朝夕光年中国官网](https://www.nvsgames.cn/)及其产品 API 使用 `nvsgames.cn`；`.com` 是全球站。
- [莉莉丝官网](https://www.lilith.com/index.html)的国服产品、账号和 PC 下载位于 `lilith.com`、`lilithgame.com`，官方静态资源使用 `lilithcdn.com`。海外发行域 `farlightgames.com` 被排除。
- [鸣潮国服](https://mc.kurogame.com/)和库洛国服资源使用 `kurogame.com`、`kurogames.com` 及 `aki-game*`；`kurogames-global.com` 进入国际层。
- [鹰角官方客服](https://customer-service.hypergryph.com/app/endfield/question/ART177649315709249426294301)直接给出 `launcher.hycdn.cn` 更新组件；[明日方舟 PC 公告](https://ak.hypergryph.com/news/7388)确认通过鹰角启动器下载和更新。
- [无限暖暖国服隐私页](https://infinitynikki.nuanpaper.com/notice/privacy)及国服页面使用 `nuanpaper.com`、`papegames.com`；海外品牌 `infoldgames.com` 被排除。

### 国内平台、渠道和合规

- [TapTap 中国](https://www.taptap.cn/about-us)、[TapTap 登录文档](https://developer.taptap.cn/docs/sdk/taptap-login/taptap-oauth/)明确区分大陆 `open.tapapis.cn` 与海外 `.com`。
- [TapTap 礼包文档](https://developer.taptap.cn/docs/sdk/tds-gift/guide/)明确大陆使用 `poster-api.xd.cn`，海外使用 `.com`。
- [九游官方下载](https://app.9game.cn/)使用 `9game.cn`。
- [vivo 应用商店/游戏中心说明](https://swsdl.vivo.com.cn/appstore/developer/staticres/4.3/doc/products/pc/index.html)证明 `vivo.com.cn` 的下载和游戏中心链路。
- [4399 游戏盒说明](https://www.4399.cn/help/FunctionIntroduce.html)和[官方下载页](https://app.4399.cn/sem/game/xmtyytfgzh-25.html)证明 `4399.cn`。
- [国家新闻出版署防沉迷接口文档](https://wlc.nppa.gov.cn/2022/02/18/a080ffa8a7ff4005b7c3dbbfcce93323.pdf)列出 `api.wlc.nppa.gov.cn` 与 `api2.wlc.nppa.gov.cn`。

## 明确排除和国际服保护

下列类型不能因为“中国公司”就整根直连：

- HoYoverse、网易、莉莉丝、库洛、鹰角、叠纸等公司的国际发行域；
- Akamai、AWS、Cloudflare、阿里云 OSS、腾讯云 COS 等共享 CDN 根域；
- `steamstatic.com`、`qcloud.com`、`myqcloud.com`、`gmertc.com` 等中外共享服务；
- AppsFlyer、Adjust、Google、Facebook 等第三方 SDK。

`InternationalGaming.yaml` 还修正了 ChinaMax 当前可能误直连的国际域，包括米哈游国际服、`bilibili.tv`、`37games.com`、海外 TapTap API，以及明确的国际 GME 主机。

## 无法仅靠网页完成的部分

真实对局常使用：

- 直接 IP；
- 动态调度的 UDP 节点；
- 共享云厂商域名；
- 客户端运行时临时下发的主机名。

因此当前规则能高置信覆盖官网、登录、启动器、补丁和已公开 CDN，但不能声称覆盖每一台对局服务器。完整的第二阶段应在中国大陆网络上分别对 PC/移动国服执行“冷启动 → 登录 → 更新 → 一局对战”，记录 DNS、SNI、目标 IP/ASN，再把只属于大陆服的新增主机逐条纳入。

配置已加入 `GEOIP,CN,DIRECT,no-resolve`，所以能被 GeoIP 正确识别的中国大陆目标 IP 会直接连接。仍需实机抓取的是未进入当前 GeoIP 数据、位于共享/海外云区或需要按游戏区分的动态节点。
