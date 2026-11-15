# 拼多多公开入口与图片主机分流研究

## 结论与当前状态

以下五个精确主机经方案审查后已接受，作为 `🛍️ 拼多多` 独立策略的完整范围，默认 `DIRECT`，保留手动代理选项。实施包含真实验证入口和公开 fixture 变异测试；不扩大到其他候选或根域。

基线为 `4840a9cd0ef6a5507c00492815af7a47a6ce6483`。五个主机在现有无 IP 元数据的域名首匹配模拟中，均命中 `ChinaMax → 🇨🇳 China-Global`，并非此前没有覆盖；独立策略提供的是更细的出口控制。

## 官方公开证据

2026-11-15 无登录读取[拼多多官网](https://www.yangkeduo.com/)和[移动商城首页](https://mobile.yangkeduo.com/)。证据为公开网页正文及网页提取器列出的实际图片链接，不是私人抓包，也不是已经确认浏览器实际发起的资源请求。未保存商品内容、账户信息、完整页面或带参数资源链接。

| 已接受精确主机 | 官方来源 | 实际观察与用途 | 证据范围 |
| --- | --- | --- | --- |
| `www.yangkeduo.com` | [官网](https://www.yangkeduo.com/) | 可读取的拼多多品牌官网入口 | 高；公开入口，不保证原生 App 使用 |
| `mobile.yangkeduo.com` | [移动商城](https://mobile.yangkeduo.com/) | 可读取的拼多多移动商城入口 | 高；仅公开首页，不验证登录或交易 |
| `commimg.pddpic.com` | 移动商城首页 | 多处实际图片链接，如 `/oms_img_ng/` 路径下的首页入口图 | 高；网页使用证据，不扩展 `pddpic.com` |
| `img.pddpic.com` | 移动商城首页 | 实际图片链接，如 `/goods/` 路径下的图片 | 高；仅该资源主机 |
| `t13img.yangkeduo.com` | 移动商城首页 | 底部导航的实际图片链接，如 `/cart/` 路径下的图片 | 高；不扩展其他图片子域 |

以上置信度只表示官方页面存在相应入口或图片引用，不代表资源主机所有权审计、拼多多独占使用、各地区可达性或原生 App 全链路覆盖。图片主机也可能供多个拼多多页面和业务使用；选代理会影响这些主机上的其他请求，不能按 URL 路径进一步隔离。

本次 `www.pinduoduo.com` 公开页面读取失败，本地直接请求也因 DNS 解析不可用而未取得原始 HTML。没有绕过验证或采用非官方规则清单补足。可读取的 `www.yangkeduo.com` 是本次明确核实的官网入口；不据此自动纳入 `www.pinduoduo.com`。

## 不纳入的范围

- 不使用 `DOMAIN-SUFFIX`、通配符或整个 `pinduoduo.com`、`yangkeduo.com`、`pddpic.com` 根域。
- 官网确有 `cdn.pinduoduo.com` 的 logo 等图片引用，以及 `images.pinduoduo.com` 的下载二维码图片引用。本次最小范围不纳入这两个较通用的官网资源主机；公开引用不等于必须为其新增独立策略。
- 移动商城存在 `promotion.pddpic.com` 的促销图片链接；为缩小非核心营销资源范围，本次不纳入，也不将这个名称直接判定为追踪服务。
- 不根据命名猜测添加 `api.pinduoduo.com`、`api.yangkeduo.com`、日志或上报主机；没有 API、登录、支付、订单、物流、定位、直播、视频或风控链路证据。
- 不采纳仅 DNS 预取、脚本白名单、社区规则或共享大型 CDN 根域作为正式范围依据；本次也没有收集这些候选。
- 不纳入 Temu、商家后台、多多买菜专用服务、推广返佣平台或其他品牌。既有安全规则保持优先，包括现有的 Temu 隐私拦截。

## 最小实施范围与验证合同

目标是为上述五个公开入口/图片主机提供可选出口，不宣称完整拼多多 App、加速、解锁、风控改善或一致出口 IP。

1. 新增 `ruleset/Pinduoduo.yaml`，只含五条固定 `DOMAIN`；在 `local-rulesets.json` 和 `catalog/services.json` 登记。目录文案使用“部分入口/图片：默认直连，可选代理”，并链接本研究。
2. 在 `config/proxy-groups.yaml` 新增唯一的 `🛍️ 拼多多` `select` 组，首选 `DIRECT`，包含 `🚀 节点选择` 手动代理选项。`config/rules.yaml` 只新增一个对应引用，放在既有安全、游戏和已添加 App 之后，`SiriAI` 及通用 Apple/媒体/GeoIP/ChinaMax 之前；不挪动现有规则。
3. 按现有模式新增 `validate_pinduoduo(root)` 并接入真实 `validate_tree(root)`。约束固定范围、重复、唯一 active 引用、顺序、唯一 select 类型和直连默认、代理选项；使用公开规则快照检查实际域名首匹配。合法 `Privacy → REJECT`、`Hijacking → 🚫 Hijacking` 可以优先命中；非安全抢占、错误安全目标、未知 provider 和不支持的顶层类型必须明确报错。所有新增文本读写显式 UTF-8。
4. 新增 `tests/test_pinduoduo.py`，在临时公开 fixture 中实际调用验证器做范围扩张、缺失/重复、引用错误、晚置、安全绕过、默认/type/代理选项、未知规则/provider 等 mutations。安全合法更新走同一 helper 验收路径。完整公开 fixture 或只读真实树哨兵验证 tree hook，不写入真实根目录。
5. 通过现有离线 `scripts/generate_catalog.py --write` 生成服务页、provider 配置与校验资产，不手改生成物。不运行网络同步，不改上游快照、Siri、权限或工作流。

### 负向对照与首匹配风险

对每个目标检查 `child.<host>`、`not<host>`、`<host>.example.org`；另检查上述三个根域、`www.pinduoduo.com`、`cdn.pinduoduo.com`、`images.pinduoduo.com`、`promotion.pddpic.com`、未核实 API/日志主机、`www.temu.com`、`pftk.temu.com`、`thtk.temu.com`、京东及 Siri 对照。比较新增规则启用/忽略时的路由，保证不属于清单的请求不改变既有路径。

现有安全及游戏 provider 目前没有抢先命中这五个目标；未来合法安全更新仍应获准通过。当前更早的已添加 App 均使用精确域名，不应抢占，但实施时须以实际规则模拟再次验证，而非仅凭规则位置判断。

手动选择代理只影响本清单；其他拼多多请求仍按旧规则走，可能出现直连与代理混合出口。如果切换后出现登录或地区识别异常，可恢复直连排查；这是条件性排错提示，不是已实测发生风控的结论。未执行账户操作、App、支付、DNS/GeoIP 或 UDP 实测。

### 验收与非目标

实施验收包括完整 tests、`scripts/validate.py`、`scripts/public_check.py`、离线目录生成一致性和 `git diff --check`，并保留原有 37 服务 / 185 tests 基线合同。不得为了通过测试放宽安全、复制其他 App 私有信息、改变已有 App、重构共享框架或增加权限。研究提交与实施提交分开；本记录本身不授权发布或合并。

## English scope summary

This ruleset contains only five exact public entry/image hosts: `www.yangkeduo.com`, `mobile.yangkeduo.com`, `commimg.pddpic.com`, `img.pddpic.com`, and `t13img.yangkeduo.com`. It defaults to DIRECT with an optional manual proxy, while security, gaming, and existing app rules retain priority. Official public-page references are evidence of use, not an authenticated app traffic capture or proof of exclusive ownership. It does not cover the complete native app, login, orders, or payments. Other requests keep their existing routes, so mixed egress is possible; selecting a proxy also affects other resources on the listed hosts. No account, private configuration, or traffic capture was accessed. Temu, broad roots, and unverified API/CDN candidates are excluded.
