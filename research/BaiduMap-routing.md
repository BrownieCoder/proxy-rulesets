# 百度地图公开入口、JSAPI 与网页资源分流研究

## 研究结论与状态

核实日期：2026-11-16。已接受首批范围为下表 4 个精确 `DOMAIN`，提供 `🗺️ 百度地图` 独立策略，默认 `DIRECT`，保留手动代理选项。以下最小计划已落实；原始研究保留为独立历史提交。

基线为 `a1c2dd26337b7277019a8764785cdf258bb6f045`，已有 41 个服务和 288 项测试。这四个候选在当前公开快照的域名首匹配模型中，均命中 `ChinaMax → 🇨🇳 China-Global`；增加的是独立出口控制，不是此前完全没有覆盖。

## 逐域官方来源与证据

只匿名读取官方公开 HTML 与开发文档，不登录、不携带浏览器 Cookie、不执行页面脚本，不请求带 AK/key 的接口，不使用位置、地址、路线或账户数据。证据只保留页面主机、标签类型及不含参数的资源路径，不保存完整页面、响应头或调用密钥。

| 已接受精确主机 | 第一方公开来源与实际证据 | 用途 / 目标 / 置信度 | 主机级影响范围 |
| --- | --- | --- | --- |
| `map.baidu.com` | [百度地图官网](https://map.baidu.com/) 返回 HTTP 200、标题为“百度地图”；[移动入口](https://map.baidu.com/mobile/) 也在同一主机。本次官网 HTML 有同主机的 stylesheet、script 和图片引用，如 `/wolfman/static/common/css/` | 官网、移动入口及同主机网页资源；默认直连，可选代理 / 高 | 匹配该主机的全部路径，不限首页或移动页面 |
| `api.map.baidu.com` | [百度地图 JSAPI 4.0 官方升级指南](https://lbs.baidu.com/docs/jsapi?title=jsapi4/upgrade) 在替换入口步骤明确以该主机 `/api` 加载 JSAPI；示例中的密钥为占位说明，本研究不复制参数或执行调用 | 官方文档声明的 JSAPI 加载入口；默认直连，可选代理 / 高 | 也影响第三方网站或应用中使用该主机的百度地图集成，不限百度地图 App，也不能按 API 路径进一步隔离 |
| `webmap0.bdimg.com` | [百度地图官网](https://map.baidu.com/) 的实际 `script[src]` 声明，路径为 `/wolfman/static/pano/com-conf_d41d8cd.js` | 官网 `/pano/` 路径的脚本资源；默认直连，可选代理 / 高 | 同主机其他页面资源也受影响；页面使用证据不证明整个主机专供某一页面或某个 App |
| `webmap1.bdimg.com` | [百度地图官网](https://map.baidu.com/) 的实际 `script[src]` 声明包含 `/wolfman/static/pano/pkg/pano-enter-pkg_c82069a.js`，另有 `/wolfman/static/pano/widget/module/PoiSearchModule/` 下的 stylesheet 引用 | 官网 `/pano/` 路径的脚本与样式资源；默认直连，可选代理 / 高 | 同主机所有路径均跟随策略；不推断整个 `bdimg.com` 或其他分片都属于本范围 |

置信度只表示官方页面确实提供入口、引用资源或在文档中声明该主机，不是所有权全面审计、浏览器实际请求抓取或原生 App 流量实测。未下载或执行上述脚本。HTML 标签证据不等于已经确认地图、全景或第三方集成的完整功能链路。

## 现有首匹配与排除项

按公开 `sources.json`、`local-rulesets.json` 和 `config/rules.yaml` 的实际顺序，使用现有 `DomainRules` 模拟；没有 IP、进程或端口元数据，不冒充 Mihomo/DNS/GeoIP/UDP 实测。

| 主机 / 对照 | 基线首条命中与策略 | 本次处理 |
| --- | --- | --- |
| 上述 4 个主机 | `ChinaMax → 🇨🇳 China-Global` | 已接受独立精确规则 |
| `ss0.bdstatic.com` | `ChinaMax → 🇨🇳 China-Global` | 官网确实引用其 `/sty/` 下三个脚本，但共享主机影响面较大，首批排除 |
| `map-mobile-static.cdn.bcebos.com` | `ChinaMax → 🇨🇳 China-Global` | 官网实际引用 `/jssdk/mapLogReport/MapLogReport.min.js`；不因日志组件引用而扩充核心地图范围，也不据名称宣称恶意或必被拦截 |
| `lbs.baidu.com`、`lbsyun.baidu.com` | `ChinaMax → 🇨🇳 China-Global` | 文档站只作来源，不作为地图运行请求加入规则 |
| `www.baidu.com` 及 `baidu.com`、`bdimg.com`、`bdstatic.com` 根域 | `ChinaMax → 🇨🇳 China-Global` | 不接管百度搜索或共享根域，不使用后缀/通配规则 |
| `hm.baidu.com` | `Privacy → REJECT` | 保留已有隐私拦截，不加入本组 |
| `log.map.baidu.com` | `ChinaMax → 🇨🇳 China-Global` | 仅作未纳入的负向对照；本次没有采集其实际请求或用途，不根据命名补齐 |
| `pan.baidu.com`、`nd-static.bdstatic.com` | `BaiduPan → ☁️ 百度网盘` | 保留网盘独立策略，不能被百度地图规则接走 |
| `webapi.amap.com` | `Amap → 🗺️ 高德地图` | 保留高德地图独立策略 |
| `guzzoni.apple.com` | `SiriAI → 🤖 AI 服务` | 保留现有 AI 精确规则 |
| `example.org` | `MATCH → 🧭 Final` | 非目标对照 |

文档站的 `mapopen-website-wiki.cdn.bcebos.com`、`mapopen-docs-assets.bj.bcebos.com` 等图像引用不证明它们是地图 App 或 JSAPI 的必要运行资源，本次不加入。共享登录、原生 SDK/API、瓦片、定位、公交、打车、语音导航、下载、支付和其他未核实资源主机均不按经验猜测补齐；没有业务需求就不为凑数量扩张分片。

## 已落实的最小实施计划

目标是让四个已核实入口/接口/资源主机可独立选出口，而不是做完整百度地图 App 清单。以下改动应在本独立分支顺序完成，共享配置有依赖，不与其他 App 同工作树并写。

1. **规则与登记。** 新增 `ruleset/BaiduMap.yaml`，只含上述 4 个精确 `DOMAIN`；登记 `BaiduMap` / `baidu-map` 本地 provider 与中文优先的出行分类服务说明。加入唯一 `🗺️ 百度地图` `select` 组，首选 `DIRECT`，保留 `🚀 节点选择` 和 `🧭 Final`。涉及 `local-rulesets.json`、`catalog/services.json`、`config/proxy-groups.yaml`，不改其他 App。
2. **实际路由顺序。** 只加一次活动引用，放在既有 App 之后、`SiriAI` / `Apple` / 媒体 / GeoIP CN / `ChinaMax` 等更宽规则之前。保留 Privacy/Hijacking、安全例外和国际/中国游戏优先，既有规则相对顺序与 `FINAL/MATCH` 不变。
3. **真实验证门禁。** 增加 `validate_baidu_map(root)` 并接入 `validate_tree(root)`。固定范围、重复与唯一 active 引用、顺序标记、默认/代理选项、缺失 provider、跨来源同名 provider、未知顶层规则均明确失败；文本读写显式 UTF-8。直接复用现有 `app_policy.validate_select_group`，不新增 type 正则或运行时 YAML 依赖，不修改共享组件和旧 App。
4. **可证明的首匹配。** 同一基础验收路径允许正确百度地图策略，或合法 `Privacy → REJECT` / `Hijacking → 🚫 Hijacking` 优先；拒绝非安全抢占、错误目标及未支持条件。域名模型无法判断的前置 `GEOIP` / `IP-CIDR` / `IP-CIDR6` 必须显式拒绝，不把跳过 IP 条件说成已验证安全。
5. **实际 fixture 回归。** 固定独立 HOSTS 与对照集；真实临时公开完整 fixture 调用 helper 和 tree 门禁，覆盖扩域/额外主机/重复、引用/顺序/默认、缺失组/provider、同名冲突、UTF-8、安全合法更新和非安全遮蔽。保留简单 select 格式正向验收，并以独立 PyYAML 测试证明复杂 type/proxies 覆盖的实际效果，确认转义、tag、anchor、显式键、merge、重复块和非法列表等均失败；不枚举转义键代替共享受限语法检查。
6. **生成与验证。** 用既有离线生成器重建 provider 配置、服务页、目录及校验资产；运行全 tests、`validate.py`、`public_check.py`、生成一致性与 `git diff --check`。检查根域、所有排除主机、网盘/高德/AI 对照以及每个正式主机的 `child.` 子域、`not` 前缀、`.example.org` 后缀在启用/忽略本组时路由不变。

验收条件是：正式范围严格 4 个主机且实际首匹配正确，所有非目标对照维持旧路由，组与 gate 唯一，生成资产一致，基线所有服务与测试保留。权限、工作流、上游快照、Siri、共享组件和许可均无变更；不运行网络同步。本研究提交不授权发布、合并或扩大范围。

## 风险与未验证项

`api.map.baidu.com` 并非只供百度地图 App 使用；手动代理会同时影响该主机上的第三方百度地图集成。也不能从 JSAPI 文档推断原生 SDK 全部使用相同主机。官网和资源主机的整台主机范围大于本次引用的单个页面路径，需接受这种主机级边界才适合纳入。

选择代理仅影响此清单，未列出的 API、瓦片、登录或其他请求继续走旧策略，同一页面或会话可能混合出口。不保证原生 App 搜索、定位、地图展示、全景、导航、账号、下载或第三方集成完整链路可用，也不改变资格、配额、地区限制或定位精度。若切换后出现登录或地区识别异常，可恢复 `DIRECT` 排查；这不是已实测风控触发或已验证解决方案。

本次没有访问真实账号、位置、行程、路线、订阅、节点、私人配置或流量；没有安装/执行 App，没有请求带 key 的 API，也未做 DNS/GeoIP/UDP 或真实设备测试。页面引用可能随时间变化，后续扩展应重新采证。

## English scope summary

The accepted scope contains four exact hosts: `map.baidu.com`, `api.map.baidu.com`, `webmap0.bdimg.com`, and `webmap1.bdimg.com`. Official website tags support the entry/resource hosts; the official JSAPI 4.0 documentation identifies the API loader host. DIRECT is the default with an optional manual proxy.

The API host also affects third-party Baidu Map integrations, not only the native app. Exact-host rules cover every path on each listed host. Shared roots, general static hosts, logging components, documentation assets, login and unverified native/SDK/tile endpoints remain excluded. Mixed egress is possible; full navigation, location, rendering or account functionality is not claimed. No private traffic, location or API credentials were used.
