# 淘宝公开入口精确分流依据

## 研究结论与边界

核实日期：2026-11-15。已接受首批范围为以下 4 个精确 `DOMAIN`，提供独立 `🛍️ 淘宝` 策略，默认 `DIRECT`，保留手动代理选择。以下实施计划已落实，原始研究仍保留在独立历史提交中。

四个主机在基线 `4840a9cd0ef6a5507c00492815af7a47a6ce6483` 的离线域名模型中均首先匹配 `ChinaMax → 🇨🇳 China-Global`。新增价值是独立控制部分公开入口，不是此前完全没有规则覆盖。

只读取匿名官方公开 HTML，不登录、不携带浏览器 Cookie、不提交表单，不访问账户、订单或支付接口。只保留不含查询参数的入口与标签证据，不保存完整页面、响应头或追踪参数。

## 逐域官方证据

| 精确主机 | 公开来源与实际页面证据 | 建议用途 / 目标 / 置信度 |
| --- | --- | --- |
| `www.taobao.com` | [淘宝官网](https://www.taobao.com/) 本次返回 HTTP 200，页面标题为“淘宝”；页面亦有回到该主机的实际链接 | 官方桌面入口；默认直连，可选代理 / 高 |
| `m.taobao.com` | [淘宝移动入口](https://m.taobao.com/) 本次请求跳转至 `www.taobao.com`，最终 HTTP 200、标题为“淘宝”；仅将该主机作为跳转入口，不称其返回独立移动页面 | 官方移动访问入口；默认直连，可选代理 / 高 |
| `pc.taobao.com` | [淘宝官网](https://www.taobao.com/) 实际 `a[href]` 目标为此主机 `/`，链接文字为“淘宝客户端”；[目标页面](https://pc.taobao.com/) 本次 HTTP 200，标题标识淘宝客户端下载 | 客户端推广/下载页面入口；默认直连，可选代理 / 高 |
| `pcdetail.taobao.com` | [淘宝官网](https://www.taobao.com/) 实际 `a[href]` 目标为此主机 `/`，链接文字为“商品”；[目标页面](https://pcdetail.taobao.com/) 本次 HTTP 200，标题标识淘宝商品网 | 商品网页入口；默认直连，可选代理 / 高 |

证据只证明官方公开入口、页面导航关系和该次响应，不代表已安装或测试原生 App，也不证明客户端下载二进制、商品详情接口、搜索、购物车、登录、购买或支付全链路覆盖。精确主机规则影响该主机的全部路径，不能只限制为首页或某种商品。

## 排除项与共享资源

- 不使用 `taobao.com`、`alicdn.com`、`taobaocdn.com` 等根域后缀或通配符。
- 官网实际引用 `g.alicdn.com` 的脚本和样式，例如路径 `/tbpc/polyfill/1.0.0/index.umd.es5.production.js`；`o.alicdn.com` 亦有 `/tbhome/tbnav/index.js` 等实际脚本引用。它们属于广泛跨业务使用的资源主机，精确匹配也会影响同主机上的其他产品，因此首批排除。
- `img.alicdn.com` 的图标/图片、`gw.alicdn.com` 的商品页面图片，以及商品页的 `g-search1.alicdn.com`、`g-search2.alicdn.com`、`g-search3.alicdn.com` 图片引用均不纳入：这里只证明淘宝页面使用，未证明淘宝专属范围。不为凑齐资源链扩大 CDN 主机清单。
- 首页 `gm.mmstat.com`、`log.mmstat.com`、`res.mmstat.com`、`dfhs.tanx.com`、`ecpm.tanx.com` 的 `dns-prefetch` 不是已完成请求或必要业务接口证据；不收录，保留既有路由与安全处理。
- `login.taobao.com`、`h5api.m.taobao.com`、其他原生接口，以及支付/安全验证主机未按猜测添加。`www.tmall.com`、`www.alipay.com` 和其他阿里业务不归入本组。
- 官网页面另链接 `goods.taobao.com`、`bk.taobao.com` 等分类或内容站；首批不扩展全部导航，等待具体使用需求和单独审查。

## 已落实的最小实施计划

目标是让上述 4 个公开入口可以独立选择出口，不改变其他主机的原路由。约束为：安全拦截、`fastcdn.hoyoverse.com` 例外、国际/中国游戏优先，既有服务相对顺序和 `FINAL/MATCH` 不变；权限、工作流、上游快照及许可不变。

1. 在现有本地规则登记和服务目录加入 `Taobao` / `taobao`；规则仅为上述 4 个精确 `DOMAIN`，增加 `🛍️ 淘宝` 的唯一 `select` 组，`DIRECT` 首选，保留 `🚀 节点选择` 和 `🧭 Final`。说明标注“部分入口：默认直连，可选代理”。
2. 活动引用放在已有国内 App 之后、`SiriAI` / `Apple` / 媒体 / GeoIP CN / `ChinaMax` 等更宽规则之前；不因 App 属于阿里而添加共享资源或关联品牌。
3. 增加真实 `validate_taobao(root)` 并由 `validate_tree(root)` 调用，覆盖精确范围与重复、活动引用唯一、必要顺序、严格单一 `select` 类型、默认直连及代理选项、缺失 provider 的明确错误、UTF-8、未知顶层规则拒绝。
4. 首匹配验收允许正确淘宝策略，或合法 `Privacy → REJECT` / `Hijacking → 🚫 Hijacking` 优先；拒绝非安全规则抢占或错误策略。不用硬编码跳过 `ChinaMax` 掩盖遮蔽。
5. 临时公开 fixture 真正调用 validator 做 mutation，另外以完整公开树只读哨兵证明 `validate_tree` 接入；使用既有生成器更新 provider 配置、服务页和目录，执行全测试、`validate.py`、`public_check.py` 与 `git diff --check`。

负向控制包含共享根域、上述 CDN/统计排除项、登录/API、天猫/支付宝、其他关联业务和 `example.org`，并对每个正式主机测试 `child.` 子域、`not` 前缀、`.example.org` 后缀；新增规则必须不命中，且移除淘宝规则前后的首匹配保持一致。

以上实施任务共享配置与验证文件，在本独立分支顺序完成，避免与其他 App 同工作树并写。当前决策：**已接受上述四主机范围，不扩展共享资源与账户链路**。

## 风险与未验证项

手动代理只影响四个入口；共享脚本、图片、接口、登录和支付继续按原规则，因此可能混合直连与代理。不能保证搜索、下载、登录、下单、支付、账号风控或地区服务可用，也不改变账户与地区资格。若切换后出现登录或地区异常，可以恢复 `DIRECT` 排查；这不是已观察到风控触发或已实测解决的结论。

离线模型不包含真实 IP/进程元数据，不能替代 DNS、GeoIP、UDP 或真实设备网络验证。页面、跳转和资源引用可能随时间变化；后续扩展必须重新采证，不自动添加整个厂商域名体系。本次没有读取私人配置、订阅、节点、账户或流量。

## English scope summary

Four accepted exact public Taobao entry hosts: the desktop homepage, mobile redirect entry, client promotion/download page, and linked product website. DIRECT is the default with an optional manual proxy. Shared Alibaba CDN hosts, login/API/payment endpoints and related brands are excluded. This is not full native-app coverage; mixed egress and all-path impact on each exact host remain possible.
