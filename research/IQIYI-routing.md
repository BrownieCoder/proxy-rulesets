# 爱奇艺公开入口精确分流研究

## 研究决定与状态

核实日期：2026-11-17。建议首批仅收录 `www.iqiyi.com` 一个精确 `DOMAIN`，提供独立 `🎬 爱奇艺` 策略，默认 `DIRECT`，保留手动代理与 Final。当前仅提交研究，等待范围审查；不改变运行规则。

官网首页和官方客户端下载介绍页共用该主机；`appstore.html` 是页面路径，不是第二个主机。不为增加规则数量，把共用安装包、图片、脚本或仅预连接主机一起归入本组。

基线为 `3ee79fedd218dc178efd91251d7fbf48ca2b8b17`，45 个服务、402 项测试。该主机在公开快照的域名首匹配中为 `ChinaMax → 🇨🇳 China-Global`，因此新增的是部分入口独立控制，不是此前完全没有规则。

## 逐主机官方证据

仅匿名读取公开 HTML，不带 Cookie，不执行脚本，不跟随安装包、登录、购买、账户或视频链接。只保留主机、标签类型与去参数路径；不保存原始网页、响应头、用户字段、媒体内容或签名 URL。

| 建议精确主机 | Primary source / 实际引用 | 用途、置信度与影响范围 |
| --- | --- | --- |
| `www.iqiyi.com` | [官网首页](https://www.iqiyi.com/)直接请求 HTTP 200，标题标识爱奇艺 iQIYI；实际 `script[src]` 和 stylesheet 指向同主机 `/static/js/`、`/static/css/`。 [官方客户端介绍页](https://www.iqiyi.com/appstore.html)直接请求 HTTP 200，标题标识爱奇艺官方客户端下载；实际 `a[href]` 指向本主机 `/`、`/appstore.html`，另有 `/cstatic/app.6a90674c.css` 样式与 `/cstatic/app/` 脚本引用 | 高：官方公开入口、同主机页面及资源引用；不代表安装包、原生 App、账号或视频链路实测。精确主机规则影响其全部路径，而不是仅首页和 appstore 页面 |

网页提取工具读取首页曾超时；正常 `curl --compressed` 直接读取成功。客户端介绍页的网页提取结果与本次直接 HTML 展示的导航/资源集合存在差异；本范围只依赖两种读取方式共同支持的官方 `www` 入口，不把页面差异描述为服务故障或作为扩大主机范围的理由。

## 有引用但不纳入的资源与入口

| 排除主机 | 本次实际证据 | 排除理由 |
| --- | --- | --- |
| `static.iqiyi.com` | 首页真实 `script[src]` 指向 `/js/player_v3/pcweb.phm.v2.js` | 只证明这条脚本被声明，不据文件名推断其是核心播放接口、必要请求或主机专属用途；本轮只控制公开入口 |
| `mesh.if.iqiyi.com` | 两页均出现 `link[rel=preconnect]` | 不是实际 API 调用或必要业务请求证据，不根据预连接猜接口范围 |
| `pic0.iqiyipic.com`、`pic1.iqiyipic.com`、`pic2.iqiyipic.com` | 客户端介绍页真实 `img[src]` 引用 `/lequ/` 下素材；`pic1` 另有图片 `a[href]` | 共用图片分片，不证明整个主机只属于主 App；首批不接管图片资源 |
| `pic3.iqiyipic.com` | 客户端介绍页实际图片 `a[href]` | 不把单个图片链接扩成整个分片主机的独立策略 |
| `dl-static.iqiyi.com` | 客户端介绍页真实下载 `a[href]` 指向 `/hz/` 下 Windows 安装包 | 只证明声明的下载目标，未请求、下载或执行；没有主机专属范围和完整重定向链证据 |
| `static-d.iqiyi.com` | 真实下载 `a[href]` 指向 `/ext/common/` 下 Mac 安装文件，另有预连接 | 主机级影响不限一个安装文件；不因一个声明补齐通用下载/静态主机 |
| `mbdapp.iqiyi.com`、`app.iqiyi.com` | 客户端介绍页真实安装包 `a[href]`；前者包含多个产品及游戏直播相关包名，后者包含电视端产品文件 | 页面聚合多个产品；不把这类主机当成爱奇艺主 App 专属，也不访问任何安装包目标 |
| `privacy.iqiyi.com`、`creator.iqiyi.com`、Apple/Huawei 应用市场主机 | 客户端介绍页实际导航链接 | 隐私、创作者及第三方商店不等于主 App 播放流量；保持原路由 |

不添加 `iqiyi.com`、`qiyi.com`、`iqiyipic.com`、`qy.net` 等根域后缀或通配符。独立游戏主机 `g.iqiyi.com` / `game.iqiyi.com`、国际站 `iq.com` / `www.iq.com`、未核实的原生 API、播放鉴权、音视频 CDN、广告和遥测端点均不猜测补齐。

**同主机边界必须接受：** `www.iqiyi.com` 本身的客户端页也实际声明了 `/cstatic/app/tracking.*.js`、`/cstatic/pingback/` 脚本；这些同主机请求会跟随本组。规则不能按路径剥离统计脚本，也不能按节目、频道、游戏推广页或其他内容区分同一主机。排除独立游戏/遥测主机，不等于声称网站自身没有相关代码或这类同主机页面完全不受影响。

## 当前首匹配与负向边界

按公开 manifests 和 `config/rules.yaml` 实际顺序复用 `DomainRules` 模拟，仅有域名，无 IP/进程/端口元数据。

| 对象 | 基线首匹配 |
| --- | --- |
| `www.iqiyi.com` 及上述已观察的其他爱奇艺静态/图片/下载/预连接主机 | `ChinaMax → 🇨🇳 China-Global` |
| `g.iqiyi.com`、`game.iqiyi.com`（只作排除对照，不声称采集了游戏请求） | `ChinaMax → 🇨🇳 China-Global` |
| `iq.com`、`www.iq.com` | `GlobalMedia → 🛰️ International-Global` |
| `msg.qy.net`（已有公开隐私快照对照） | `Privacy → REJECT` |
| `v.qq.com`、`m.v.qq.com` | `TencentVideo → 📺 腾讯视频` |
| `www.bilibili.com` | `Bilibili → 📺 Bilibili` |
| `www.alipan.com` | `AliPan → 📁 阿里云盘` |
| `guzzoni.apple.com` | `SiriAI → 🤖 AI 服务` |
| `example.org` | `MATCH → 🧭 Final` |

不将国际站改归国内策略，不绕过当前或未来合法隐私/劫持拦截。后续测试对根域、排除主机、其他已合 App，以及 `child.www.iqiyi.com`、`notwww.iqiyi.com`、`www.iqiyi.com.example.org` 等边界比较启用/移除本组的首匹配，均须不变。

## 最小实施计划（待批准）

目标只是在局部公开入口增加独立可选出口；非目标是完整网站/原生 App、安装包、图片、播放、登录、会员购买、版权/地区资格或账号风控效果。

1. 新增 `IQIYI` / `iqiyi` 本地 provider、仅一条固定 `DOMAIN,www.iqiyi.com`、独立 `🎬 爱奇艺` `select` 组，`DIRECT` 首选且保留 `🚀 节点选择` 与 `🧭 Final`。目录写“单个公开入口：默认直连，可选代理”，保留逐域来源及 all-path / mixed-egress 限制。涉及本地 manifest、catalog、策略组、有序规则和规则文件。
2. 活动引用唯一，位于全部 17 个已合 App 之后（包含百度地图、快手、腾讯视频、阿里云盘），并位于 SiriAI/Apple、YouTube/Bilibili/TikTok/Disney/Netflix 五媒体、GlobalMedia、GeoIP/ChinaMax 之前。安全、国际/中国游戏、例外及既有规则相对顺序、FINAL/MATCH 不动。
3. 增加 `validate_iqiyi(root)` 和真实 `validate_tree` hook。复用原有 `app_policy.validate_select_group`，不手写 type regex、不改共享组件或旧 App；严格固定范围/重复/唯一引用/活动顺序、DIRECT/manual proxy/Final、UTF-8、未知和缺失 provider、manifest 同名冲突、未知/不完整顶层条件、前置 IP/GeoIP fail-closed。
4. 独立固定 HOSTS 与负控，真实完整公共 fixture 实调 helper 和 tree：先证明完整树可通过，再做范围、引用、全部前驱/后继、默认/组缺失、provider、IP、未知句法、复杂 type/proxies 和合法 select 格式等变异。正确 `Privacy → REJECT` 或 `Hijacking → 🚫 Hijacking` 未来优先命中走同一验收路径；非安全抢占或错误目标拒绝，不硬编码跳过 ChinaMax 或要求永远必须命中新 App。
5. canonical 顺序实施后只用既有离线 generator 重建资产，执行针对性及全量测试、validate、public_check、生成一致性、diff 和旧函数/共享/来源/权限保护检查。共享配置有依赖，应在本独立分支顺序完成，不能与其他 App 同工作树并写。

验收需保留 45 服务 / 402 测试基线及全部已合规则，仅新增本 App；权限、工作流、共享模块、上游镜像、Siri、许可不变，不运行同步。当前决定：等待范围批准，研究本身不授权发布或合并。

## 使用与验证限制

手动代理只影响这一个主机，未列出的接口、资源和媒体请求继续旧策略，同一页面/会话可能混合出口。本组不保证加载、下载、播放、清晰度、会员、账号或地区功能，也不改变版权或资格；若切换后出现登录/地区异常，可先恢复 DIRECT 排查，这只是条件性建议，不是已观测风控或已实测修复。

未登录、播放、订购、下载或执行客户端，没有用户流量、账户字段、私有配置、节点或订阅；没有实际 DNS、GeoIP、UDP、设备或播放验证。页面可能更新，后续扩域需重新采证。

## English scope summary

The proposed scope is one exact host, `www.iqiyi.com`, covering the official portal and its `/appstore.html` client-introduction page. Actual same-host links, scripts and styles support this entry; no extra host is needed merely because appstore is a second page. DIRECT is the proposed default with optional manual proxy and Final.

All paths on that host are affected, including same-host tracking/pingback scripts or other product/channel pages. Independent game/telemetry hosts, international `iq.com`, shared pictures, installers, preconnect-only interfaces and unverified media/API endpoints remain excluded. Other requests retain their routes, so mixed egress is possible. This is not full native-app, download, playback or region/copyright control. No account, private traffic, purchase, installer or video request was used. Implementation awaits scope approval.
