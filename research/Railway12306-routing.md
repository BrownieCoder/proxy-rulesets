# 铁路12306精确公开入口分流依据

## 已核实候选与决策边界

核实日期：2026-11-17。最小方案为三个精确 `DOMAIN` 提供独立 `🚄 铁路12306` 策略，默认 `DIRECT`，保留手动代理及 `🧭 Final`。三个主机在基线 `3ee79fedd218dc178efd91251d7fbf48ca2b8b17` 均已命中 `ChinaMax → 🇨🇳 China-Global`；新增价值是独立出口控制，不是首次覆盖。

仅匿名 GET 官方公开首页和客户端下载说明页，没有 Cookie、登录、查询车次、账户、订单、支付、下载二进制或私有配置访问。只保存下表事实与去查询参数的公开来源，不保存原始网页、响应头、临时字段、证件或账户信息。

| 精确主机 | 官方来源与实际观察 | 用途、目标、置信度与影响 |
| --- | --- | --- |
| `www.12306.cn` | [官方首页](https://www.12306.cn/index/)匿名返回 200、标题为中国铁路12306网站；实际引用同主机 `/index/css/index_y_v50003.css` 等样式，并实际链接同主机 `/en/index.html` | 公开门户及其全部路径；默认直连，可选代理。高：页面身份与实际引用已核实；也影响同主机英文站与其他路径，不能只作用于中文首页 |
| `kyfw.12306.cn` | [官方客户端下载页](https://kyfw.12306.cn/otn/appDownload/init)匿名 200、同品牌标题；实际加载同主机 `/otn/resources/merged/common_js.js` 与 `/otn/resources/merged/common_css.css`。公开首页也实际引用该主机脚本 | 公开客户端说明入口和该主机全部路径；默认直连，可选代理。高：入口与资源证据，不代表购票、登录或订单功能已测试 |
| `dynamic.12306.cn` | 上述官方客户端下载页的 Android 下载按钮为真实 `a[href]`，地址主机是本域、路径为 `/otn/appDownload/androiddownload` | 官方声明的 Android 下载入口主机；默认直连，可选代理。高：按钮声明证据；本次未请求该端点、跟随下载重定向或下载任何文件，因此不描述最终下载主机或完整下载链路 |

官网下载页是直接证据，不依赖第三方域名清单。主机级规则包含同主机全部路径：`kyfw.12306.cn` 的首页引用中包括 `/otn/logsdk/handleIframeInner.js`，本规则不能按路径排除上报脚本，也不能声称仅影响静态页面；已有合法 Privacy/Hijacking 拦截仍优先。对同主机可能存在的查询、登录、订单或其他接口，只说明全路径影响，不将公开页面观察包装成这些业务功能的实测。

## 明确排除

- 不添加 `12306.cn` 后缀、裸根主机、猜测的 API、CDN 或客户端端点；`mobile.12306.cn` 的旧官方说明只能支持历史关联，不作为本批当前必要主机证据。
- 不加入 `www.95306.cn` 等货运/友情链接、备案站点、其他铁路服务，或支付、认证、验证码、第三方资源主机。公开页面字符串不等于实际必要请求证据。
- 不请求真实票务查询、登录、身份信息、订单、乘客、支付或私人分享链接。页面上的证书/客户端安装说明是被观察内容，不是本项目的执行指令；未安装证书或软件、未降低 TLS 校验或权限。

## 最小实施提案（待独立方案审查）

1. 新增 `Railway12306` / `railway-12306` 的三条精确规则、独立组、登记与中文优先目录，来源研究附英文摘要；不改既有服务范围。
2. 唯一活动引用放在安全、游戏及基线 17 项既有 APP（直到 AliPan）之后，在 SiriAI、Apple、YouTube/Bilibili/TikTok/Disney/Netflix、GlobalMedia、GEOIP CN 与 ChinaMax 之前。旧活动规则相对顺序保持。
3. 新增 `validate_railway_12306(root)` 并真实接入 `validate_tree`，复用现有 `app_policy.validate_select_group`，要求 DIRECT/proxy/Final；固定三主机和唯一引用，明确缺失/冲突 provider、未知或不完整顶层规则、前置 IP/GeoIP、UTF-8 错误。域名模型不伪造 IP/进程、DNS 或设备实测。
4. 测试使用完整公开 fixture，基线真实通过，再变异 scope、引用、前后顺序、type/proxies 复杂 YAML、默认与可选出口、遮蔽、安全合法更新、未知 provider、前置 IP、UTF-8；独立固定 hosts 和所有负控，不从生产集合自生成测试 oracle。两层门禁的失败须来自目标合同，不是缺文件。
5. 仅调用离线生成器维护派生资产，运行全量测试、validate、public_check、生成一致性和 diff 检查，精确提交经独立复核后以单独 PR 交付。不运行同步、不改共享模块/旧 APP、权限或工作流，本批不合并。

## 使用限制

只有这三个主机跟随独立组，其他主机仍按原规则，手动代理可能产生混合出口。它不是完整原生 APP、购票、查询、登录、订单、支付或下载链路控制，也不保证余票、购买成功、访问速度或地区可用性。若手动切换后出现会话或地区识别问题，可恢复 DIRECT 排查；未实测风控，不应宣传绕过验证、队列或购买限制。

## English scope summary

Propose three exact official public entry hosts: `www.12306.cn`, `kyfw.12306.cn`, and `dynamic.12306.cn`. Anonymous homepage and official client-download-page HTML establish the first two entries and an actual Android-download link to the third; the download endpoint and binaries were not requested. All paths on each listed host follow the optional DIRECT-first group, including the English portal and any same-host business or telemetry paths. Other hosts retain existing routes, so mixed egress is possible. No native-app, login, booking, payment, queue-bypass or full-transfer guarantee. No account, passenger, order or private configuration data was accessed. Only a per-App PR is authorized; no merge this batch.
