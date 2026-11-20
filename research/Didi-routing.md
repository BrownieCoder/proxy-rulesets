# 滴滴出行公开官网入口精确分流依据

核实日期：2026-11-21。基线：`9b0a5eb64c9a241b1bcd049c8526af7c97768571`。

## 官方证据与范围

只匿名读取公开网站和商店页面，不登录、不发起订单或付款、不下载客户端或保存原始流量。商店支持链接是开发者提供的归属证据，并非商店认证该主机仅供此 App 使用。

| 精确主机 | 官方来源及本轮观察 | 决定 |
| --- | --- | --- |
| `www.didichuxing.com` | [DiDi China: Ride Hailing 官方发行页面](https://play.google.com/store/apps/details?id=com.sdu.didi.psnger)的应用支持网站明确链接到 [www.didichuxing.com](https://www.didichuxing.com/)。本轮网页读取返回另一主机 `www.didiglobal.com` 的首页 | 纳入高置信度开发者声明的初始入口。不将一次网页读取描述为固定重定向链、状态码或地区行为 |
| `www.didiglobal.com` | [滴滴官网](https://www.didiglobal.com/)为本轮观察到的落地主机。[滴滴快车官方产品介绍](https://www.didiglobal.com/travel-service/express)同主机，提供乘客端下载入口；未点击下载 | 纳入高置信度官网及本轮落地主机。只做精确 `DOMAIN`，不是客户端必要连接清单 |

[中国 App Store 的滴滴出行发行页](https://apps.apple.com/cn/app/id554499054)独立支持产品身份，其开发者隐私链接到 `page.udache.com`；Google Play 的隐私链接到 `s.didi.cn`。两个隐私主机均非本批官网入口，不纳入。官网及产品页在网页工具中的获取时间不同；网页身份和一次跳转观察不替代实时 HTTP 或网络测量。

两目标主机上的全部路径随策略，包括同主机的司机、企业、集团或境外服务介绍，不支持只对大陆乘客或特定页面分流。裸根 `didichuxing.com` / `didiglobal.com`、[香港站](https://hk.didiglobal.com/)、[墨西哥站](https://mexico.didiglobal.com/)、[投资者网站](https://ir.didiglobal.com/)、其他地区、镜像、共享图文主机或推测的 API 均不纳入；不添加整个集团后缀、通配符或 IP。未收录主机沿原策略，切换出口可能出现混合路由；若出现异常可恢复 DIRECT 排查，未实测风控。

## 既有路由与验证

在公开 manifests、payload 及有序模板上进行纯域名首匹配模拟。两个目标和上述地区、隐私、投资者主机均为 `ChinaMax → 🇨🇳 China-Global`，对照 `example.org` 为 `MATCH → 🧭 Final`。新增价值是两个官网入口有独立、默认 DIRECT 的出口选择，不是首次覆盖或修复现有网络故障，也不能据公共模板的策略名推断用户实际出口。

唯一 `RULE-SET,Didi,🚕 滴滴出行` 位于安全、游戏及既有独立 App（含微博）之后，SiriAI、Apple、综合媒体、ChinaMax 等之前。保留既有规则相对顺序、策略选项和 MATCH，生成器同步目录、provider 模板和散列。针对两域、拼接/嵌套负控、同服务非目标、真实先匹配、合法安全拦截、错误提前命中、未知规则/提供者及无效策略组进行公开临时 fixture 验证。

域名模拟按 [Mihomo 固定源码版本的 DOMAIN 构造](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L33)对域名条件逐字符转小写；包括 [Go 将 U+0130 映射为 ASCII `i`](https://go.dev/src/unicode/tables.go) 的情况，不做 IDNA 或其他折叠，策略名保持字面值。

这不是完整原生 App、司机、地图定位、叫车、订单、支付、登录、实时行程或海外链路覆盖，不保证服务可用性、风控、价格或资格。未实测 DNS、GeoIP、UDP、原生客户端或个人行程。

## English scope summary

Include only the exact public web entries `www.didichuxing.com` (developer-declared Google Play support website) and `www.didiglobal.com` (the observed landing host and official ride-service website), with a DIRECT-first optional policy. All paths on those hosts follow the group, including corporate, driver and international content on the same sites; this is not a regional or path split. Other regional sites, apex names, privacy, shared assets and unverified API hosts retain their existing routes, so mixed egress remains possible. This does not cover the complete native app, account, ride, location, payment or trip flow. Verification used only public sources and offline fixtures.
