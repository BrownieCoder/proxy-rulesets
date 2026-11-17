# 闲鱼公开入口精确分流研究

## 状态与最小建议

研究日期：2026-11-17。已接受范围仅 3 个精确主机：`goofish.com`、`www.goofish.com`、`terms.goofish.com`。新增 `Xianyu` / `xianyu` 与独立 `🐟 闲鱼` 策略，默认 `DIRECT`，保留手动 `🚀 节点选择` 和 `🧭 Final`。范围及最小方案已独立核实后接受，实施不扩大下述边界。

基线 `3ee79fedd218dc178efd91251d7fbf48ca2b8b17` 已含 45 项服务、402 项测试。3 个候选都已命中 `ChinaMax → 🇨🇳 China-Global`，新增价值是独立出口控制，不是此前完全没有覆盖，也不是补齐整个闲鱼原生 App。

## 官方证据与逐主机边界

只匿名读取公开首页、App Store 开发者元数据和公开隐私声明，以及相应公开重定向头。不登录、不携带现有 Cookie，不查询商品、买卖双方、消息、订单或账号，也不下载 App。使用标准响应解压，不执行页面脚本或绕过访问控制；普通网页读取器对根入口曾超时，直接匿名 HTTPS 可核实下列状态，不把超时作为扩域理由。

| 精确主机 | 原始官方来源与实际证据 | 用途、目标与置信度 | 主机级影响与限制 |
| --- | --- | --- | --- |
| `www.goofish.com` | [公开官网](https://www.goofish.com/)实际 HTTP 200，HTML 标题标识闲鱼；真实 `a[href]` 指向同主机 `/login`、`/search`、`/im`、`/mach-feeds`，只提取标签路径，未进入这些功能 | 公开网站入口；默认直连，可选代理。高：公开首页和同主机导航声明 | 整个主机的所有路径均跟随该组，包括可能承载的登录、搜索、消息和商品页面；不能承诺这些功能的其他请求也跟随 |
| `goofish.com` | [开发者 App Store 页面](https://apps.apple.com/cn/app/id510909506)的“开发者网站”实际 `a[href]` 指向[根入口](https://goofish.com/)；独立匿名 HEAD 返回 301、`Location` 为 `https://www.goofish.com/`，跟随这一公开跳转后 HTTP 200、品牌标题一致 | 官方声明的别名 / 重定向入口；默认直连，可选代理。高：开发者元数据与实际重定向交叉核实 | 精确根主机本身，不是 `DOMAIN-SUFFIX,goofish.com`；其余子域不会因此被接管 |
| `terms.goofish.com` | 同一 [App Store 页面](https://apps.apple.com/cn/app/id510909506)实际隐私政策链接指向[闲鱼社区隐私政策](https://terms.goofish.com/legal-agreement/terms/suit_bu1_taobao/suit_bu1_taobao202103021554_43790.html)；该公开路径匿名 HTTP 200，实际 HTML 标题与政策标题一致 | 官方公开条款入口；默认直连，可选代理。高：开发者声明和实际公开页面 | 规则影响整个条款主机，不只上述隐私页面；不能把公开声明的身份等同原生 App 全链路观测 |

App Store 提供的开发者网站、隐私链接是开发者元数据，不是 Apple 对主机独占性或功能可用性的独立认证。置信度只指公开关联证据，不保证所有地区、时刻或客户端的访问结果。

## 已见共享资源与不纳入范围

官网 HTML 实际 `script[src]` / `link[href]` 包含 `g.alicdn.com` 的 `/idle-pc/xy-site/0.0.184/js/main.js` 与相应 `p_index`、`p_layout` 脚本/样式，也包含通用 React 资源。`gw.alicdn.com` 的 `img[src]` 为品牌图片，`img.alicdn.com` 有图标声明，`o.alicdn.com/vip/goofish-auto-login/plugin.js` 为实际脚本标签。即使路径明确与闲鱼有关，这些主机仍是共享阿里基础设施，本批不把整台主机改归闲鱼，也未执行自动登录脚本。

首页还为 `gm.mmstat.com`、`log.mmstat.com` 声明预连接线索；这不是核心业务请求证据，不把上报主机加入规则。`g.alicdn.com`、`gw.alicdn.com`、`img.alicdn.com`、`o.alicdn.com` 的预连接本身也不构成扩域理由。

隐私声明中还可见 `h5.m.goofish.com` 的个性化设置链接及淘宝、共享条款站链接。它们只证明页面声明了特定功能入口，本次不打开账号设置、不执行操作，也不由这些线索扩为 H5 / 原生客户端覆盖。

不增加 `DOMAIN-SUFFIX,goofish.com` 或任何阿里根域、共享 CDN；未核实的登录、鉴权、聊天、图片上传、商品 API、支付、下单、物流、下载和分享端点均不猜测。淘宝、支付宝、阿里云盘以及其他已合服务不归入本组。安全拦截保持优先，根入口和政策不必为了“完整 App”而带入关联平台。

## 基线首匹配与非目标对照

读取公开 manifests、规则文件和现有 `siri_ai.DomainRules`，按实际活动顺序进行无 IP / 进程元数据的离线域名模拟：

| 目标或对照 | 基线首条命中 |
| --- | --- |
| `goofish.com`、`www.goofish.com`、`terms.goofish.com` | `ChinaMax → 🇨🇳 China-Global` |
| `h5.m.goofish.com`、4 个上述阿里 CDN 主机、`www.alipay.com` | `ChinaMax → 🇨🇳 China-Global` |
| `gm.mmstat.com`、`log.mmstat.com` | `MATCH → 🧭 Final`；不宣称当前已被 Privacy 拦截 |
| `www.taobao.com` / `www.alipan.com` | `Taobao → 🛍️ 淘宝` / `AliPan → 📁 阿里云盘` |
| `pan.baidu.com` / `map.baidu.com` | `BaiduPan → ☁️ 百度网盘` / `BaiduMap → 🗺️ 百度地图` |
| `www.kuaishou.com` / `v.qq.com` | `Kuaishou → 📹 快手` / `TencentVideo → 📺 腾讯视频` |
| `guzzoni.apple.com` / `example.org` | `SiriAI → 🤖 AI 服务` / `MATCH → 🧭 Final` |

正式范围的 3 个精确 `DOMAIN` 不应匹配各自的 `child.`、`not…` 或 `….example.org` 变体。首匹配验证还应证明保留现有 / 未来合法 Privacy、Hijacking 优先命中，并拒绝非安全规则遮蔽；不能只检查规则文件存在。测试中的 `m.goofish.com`、`api.goofish.com` 和 `goofish.cn` 仅为命名边界负向对照，不声称观察到它们的业务请求。

## 已接受的最小实施范围

目标是官网 / 官方重定向 / 公开条款入口的独立选择，不改变其余流量。

1. 仅新增 `ruleset/Xianyu.yaml` 的 3 条固定 `DOMAIN`、本地登记、目录说明和 `🐟 闲鱼` DIRECT-first select。涉及 `local-rulesets.json`、`catalog/services.json`、`config/proxy-groups.yaml`，不改旧服务内容。
2. 活动引用唯一，放在基线全部 17 个既有 App（最后为 AliPan）之后，SiriAI、Apple、YouTube / Bilibili / TikTok / Disney / Netflix、GlobalMedia、GeoIP CN、ChinaMax 之前。安全优先、InternationalGaming → ChinaGaming、FINAL / MATCH 及既有相对顺序不变。
3. 只新增 `validate_xianyu(root)` 和一次真实 `validate_tree` 调用，复用 `app_policy.validate_select_group`。固定范围 / 重复 / 唯一引用 / 顺序 / 默认与可选出口，拒绝 manifest 同名冲突、未知或缺失 provider、未知顶层类型、未完整条件，以及新引用之前的任何 GEOIP / IP-CIDR / IP-CIDR6（域名模型没有对应元数据）。
4. 增加真实完整公共 fixture 的正向通过和变异回归：合法 / 复杂策略语法、Final、17 项前驱与媒体后继、前置 IP、provider 错误、UTF-8、合法安全更新和非安全遮蔽。独立固定 HOSTS 与全部已审负向对照，跨淘宝 / 支付宝 / 阿里云盘 / 百度地图 / 快手 / 腾讯视频 / Siri 对照不变。
5. canonical 改完后只运行现有离线生成器，验证规则 / 公开内容 / 生成一致性 / diff、专项与完整测试，再交独立精确提交复核。研究和实施分开提交，每个 App 独立 PR；本分支不 push 或 merge，由维护者按本批“不合并”限制交付。

风险为同主机全路径影响、共享资源留在旧策略造成混合出口，以及未来官方主机变化。证据不足时减少范围，不通过共享后缀、私人流量或登录态补齐。本次不重构旧 App、共享组件或网络模型，也不修改权限、工作流、快照、许可或执行联网同步。

## 使用与验证边界

切换代理只移动 3 个精确入口主机的全部路径。其他 H5、鉴权、图片、API、聊天、订单、支付、物流和原生 App 请求继续原策略，可能形成混合出口；不保证登录、搜索、消息、发布、交易或原生 App 全链路，也不改变账号、风控、地区、支付或交易资格。

未实测 DNS、GeoIP、UDP、登录或交易。若自行切代理后遇到登录或地区识别异常，可恢复 DIRECT 排查；这是条件性建议，不是已实测风控结论。不要向 issue 上传完整私人配置、节点、订阅、Cookie 或买卖双方数据。

## English scope summary

Include only three exact official Xianyu entry hosts: `goofish.com`, `www.goofish.com`, and `terms.goofish.com`. Anonymous official HTML, the developer-supplied App Store website/privacy links, and an observed apex-to-www 301 redirect support this accepted scope. Default DIRECT with manual proxy and Final options adds independent control; these hosts already match ChinaMax.

All paths on each listed host are affected. Shared Alibaba CDN/telemetry, H5 settings, unobserved API/auth/chat/order/payment endpoints and other products stay on their existing routes. No full native-app, login, messaging or transaction-chain coverage, or account/payment/region unlock claim. Only public pages were read; no account, installer, buyer/seller data or private traffic was accessed.
