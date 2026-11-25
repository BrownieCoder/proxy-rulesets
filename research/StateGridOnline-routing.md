# 网上国网公开入口分流依据

基线：`c594b80a278cc48e4e363747a9627d8b2bae29be`。新增 `DOMAIN,www.95598.cn`，对应 `⚡ 网上国网` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [95598 官方门户](https://www.95598.cn/)：入口本次跳转到同一主机的 `/osgweb/`，匿名读取见 95598 智能互动网站页面提示；未验证页面内交互。
- [网上国网官方隐私政策](https://95598.cn/app/statement/userPrivacyPolicy.html)：明确该 App 及其 `www.95598.cn` 网址；协议所在裸域不另纳入。
- [中国区 App Store](https://apps.apple.com/cn/app/id1438998315)：国家电网有限公司客户服务中心的开发者网站链接也指向 `www.95598.cn`。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未安装客户端、登录或采集流量。

## 作用与边界

同主机所有路径均随组；裸域、国网企业官网和独立隐私资源不另纳入。未验证原生 App、登录、办电、缴费、账单或充电链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`95598.cn`、`sgcc.com.cn`、`www.sgcc.com.cn`、`csc-static.sgcc.com.cn`、`www.189.cn`、`www.10086.cn`、`www.10010.com`、`guzzoni.apple.com`、`example.org` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.95598.cn` gets a dedicated DIRECT-first selector for State Grid Online. All paths on that hostname follow the selector; other hosts keep their existing routes. This is not full native-app coverage; live network and client behavior were not tested.
