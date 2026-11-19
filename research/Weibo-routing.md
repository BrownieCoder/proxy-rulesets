# 微博公开入口精确分流依据

核实日期：2026-11-19。基线：`70c33529edef85b38eb845a7edf96cccea06067c`。已接受范围仅 `DOMAIN,weibo.com` 与 `DOMAIN,www.weibo.com`；provider `Weibo`、目录 id `weibo`、分类“社交”，独立 `🟠 微博` DIRECT-first select，保留现有代理和 Final。

## 官方证据与观察限制

只匿名读取官方公开入口、服务协议和开发者元数据，不登录、不执行页面脚本、不访问个人内容或账号接口，也不获取安装包。以下证据说明入口归属，不证明客户端完整流量或功能可用性。

| 精确主机 | Primary source 与实际观察 | 置信度、用途及限制 |
| --- | --- | --- |
| `www.weibo.com` | [国内微博 App Store 页面](https://apps.apple.com/cn/app/id350962117)列明开发者 SINA Corporation，其“开发者网站”实际链接指向 `https://www.weibo.com/`。打开此链接后，网页读取返回 `https://weibo.com/us`，标题“微博北美站”。[同主机服务协议](https://www.weibo.com/signup/v5/protocol)及[隐私政策](https://www.weibo.com/signup/v5/privacy)可读 | 高置信官方声明入口；开发者声明不等于 Apple 对主机独占性或服务可用性的认证。保留初始入口与落地入口的独立出口选择，不声称此跳转在所有地区或时间稳定成立 |
| `weibo.com` | [直接首页](https://weibo.com/)的网页读取也返回同主机 `/us` 页面；[服务协议](https://weibo.com/signup/v5/protocol)识别为微博服务使用协议 | 高置信公开网站入口及本次观察的落地主机。不能由此推断国内首页、登录状态、重定向状态码或服务端地域识别机制 |

网页工具给部分官网结果标记约四个月前抓取，App Store 元数据标记为本次读取；本研究不把缓存观察冒充实时 HTTP 测量。另一次标准库匿名 HTTPS 交叉读取因本环境 DNS 解析失败，未取得 HTTP 响应，不能据此说站点失效。没有保存原始网页、响应头、Cookie 或带查询参数的访客地址。

## 暂不收录的官方移动入口与其他边界

App Store 的真实“隐私政策”链接指向 `https://m.weibo.cn/c/privacy`，开发者说明也声明该地址，足以证明其官方关联。然而，本次打开该页及移动首页只观察到跨主机 `visitor.passport.weibo.cn` 的 `/visitor/visitor` 访客系统，没有取得移动页面可读正文。本批不纳入 `m.weibo.cn`，也不追随或模拟访客验证、认证、Cookie 初始化；这不是否认其官方身份或断言移动站不可用。

- 不添加 `DOMAIN-SUFFIX,weibo.com`、整个 `weibo.cn`、新浪/CDN 根域或其通配符。
- 首页链接出现的 `d.weibo.com`、`vip.weibo.com`、`photo.weibo.com`、`game.weibo.com`、`data.weibo.com`、`kefu.weibo.com` 不纳入；相关产品或链接存在不代表本批应接管它们。
- `passport.weibo.com`、`api.weibo.com`、`m.weibo.com` 等名字仅作未收录的形状负控，不宣称抓到了这些业务请求；`sina.com.cn`、`sinaimg.cn`、`sinajs.cn`、`weibocdn.com` 及素材子域也不因为品牌关联进入本规则。
- 两个 exact 主机的全部路径都随策略，包括地区页、条款、隐私及同主机可能存在的账号、会员、推广、内容或其他路径；DOMAIN 不能按页面、用户或用途隔离。
- 其他主机仍走原策略，手动代理可能混合出口；切换后若会话或地区异常，可恢复 DIRECT 排查，未实测风控。不能保证保持国内页面、绕过访客验证，或获得完整原生 App、登录、图片/视频、发布、私信、API、下载、会员及地区资格。

## 现有首匹配与新增价值

只用公开 manifests 与有序模板进行无 IP、进程或端口元数据的离线域名模拟：

| 对象 | 基线首匹配 |
| --- | --- |
| `weibo.com`、`www.weibo.com` | `ChinaMax → 🇨🇳 China-Global` |
| 移动入口、访客验证、其他微博子域及所列新浪素材负控 | `ChinaMax → 🇨🇳 China-Global` |
| `weibo.com.example.org` | `ChinaMax → 🇨🇳 China-Global`，不是 MATCH |
| `example.org` | `MATCH → 🧭 Final` |
| `guzzoni.apple.com`、`hmma.baidu.com`、`fastcdn.hoyoverse.com` | 分别为 SiriAI、Privacy/REJECT、既有 exact DOMAIN/DIRECT |

现有 ChinaMax 镜像同时含 `DOMAIN-SUFFIX,weibo.com` 和 `DOMAIN-KEYWORD,weibo`。新增规则的价值是两个入口的独立出口选择，不是首次覆盖，也不证明旧规则故障；不能据公共策略名称推断用户私有配置选择了哪个出口。伪子域负控只比较新增前后是否不变，不硬编码它必须走 MATCH。

## 接入与验证合约

唯一引用在全部 25 个既有 App（含 WPS Office、飞书、钉钉和夸克）之后、SiriAI 之前；保留旧规则与策略组相对顺序、安全与游戏优先、Gemini/Google 及 MATCH。只增加本 App validator/tree hook，复用既有受限规则、策略组模型和 select 门禁，不修改旧函数、共享模块、镜像、来源锁、依赖、工作流或权限。生成资产只由现有离线生成器维护。

验收固定两个 HOSTS、全部排除负控和真实首匹配；允许正确 Privacy/REJECT 或 Hijacking/拒绝优先，拒绝非安全抢先及错误目标。完整公开临时 fixture 既需原样通过，也需对范围、重复、引用、顺序、选项、复杂 YAML、错误/重复根、provider、未知/不完整/空白规则和前置 IP 条件真正拒绝；合法 select 格式与安全更新仍通过。新增直接入口加入公共结构测试列表，结构错误使用准确原因，不为保留旧 App 前缀放宽断言。离线模型不替代 DNS、GeoIP、代理连通性或真实客户端验证。

## English scope summary

Accepted scope: only the two exact public entry hosts `weibo.com` and `www.weibo.com`, with an optional DIRECT-first group. The official Chinese App Store developer website links to `www.weibo.com`; the page reader returned `weibo.com/us`, and official same-host terms/privacy pages support attribution. Some website responses are cached observations, not fresh HTTP measurements or a guarantee of stable redirection, a domestic landing page, or regional behavior.

The officially declared mobile privacy host is excluded from this batch after only a cross-host visitor-system response was observed. No visitor/authentication flow is reproduced. Other Weibo subdomains, shared Sina/CDN resources and unverified APIs stay on their existing routes. All paths on the two included hosts follow the group, so mixed egress remains possible; no complete native-client, login, media, membership or regional-eligibility claim is made. Public fixtures and offline checks contain no private configuration, account traffic, tokens or subscription data.
