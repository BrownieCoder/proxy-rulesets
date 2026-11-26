# 网上国网公开入口分流依据

基线：`c594b80a278cc48e4e363747a9627d8b2bae29be`。新增 `DOMAIN,www.95598.cn`，对应 `⚡ 网上国网` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [95598 官方门户](https://www.95598.cn/)：入口本次跳转到同一主机的 `/osgweb/`，匿名读取见 95598 智能互动网站页面提示；未验证页面内交互。
- [网上国网官方隐私政策](https://95598.cn/app/statement/userPrivacyPolicy.html)：明确该 App 及其 `www.95598.cn` 网址；协议所在裸域不另纳入。
- [中国区 App Store](https://apps.apple.com/cn/app/id1438998315)：国家电网有限公司客户服务中心的开发者网站链接也指向 `www.95598.cn`。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未安装客户端、登录或采集流量。

## 作用与边界

发往 `www.95598.cn` 的所有请求均随组，包括公开索引中的分布式光伏机制电价竞价操作手册（路径 `/omg-static/omg-static/99310311749014888233401083463870.pdf`）。本次未验证文件下载；若请求跳转到其他主机，则按目标主机重新匹配。裸域 `95598.cn` 上的隐私政策、国网企业官网和独立隐私资源不纳入，保留原路由。未验证原生 App、登录、办电、缴费、账单或充电链路。规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`95598.cn`、`sgcc.com.cn`、`www.sgcc.com.cn`、`csc-static.sgcc.com.cn`、`www.189.cn`、`www.10086.cn`、`www.10010.com`、`guzzoni.apple.com`、`example.org` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.95598.cn` gets a dedicated DIRECT-first selector for State Grid Online. Requests to any path on that hostname, including public PDF paths under `/omg-static/`, follow the selector. Redirects to another hostname are matched separately, and the privacy policy on bare `95598.cn` keeps its existing route. File downloads and native-app behavior were not tested.
