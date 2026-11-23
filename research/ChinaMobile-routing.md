# 中国移动公开入口分流依据

基线：`31d0baa1da42d02d9b97d6399ad4fc3a4bf1a40b`。新增 `DOMAIN,wap.10086.cn`，对应 `📱 中国移动` 策略组，默认直连（DIRECT），可手动选择节点或 Final。

## 官方依据

- [中国移动官方服务中心](https://www.10086.cn/support/service/channel/mobile/index.html)：列出 wap.10086.cn 作为中国移动客户端下载入口和 WAP 掌上营业厅。
- [中国 App Store](https://apps.apple.com/cn/app/id583700738)：确认中移在线发行的中国移动 App。

证据级别：第一方公开网页或开发者在应用商店提供的资料。证据支持主机归属及公开入口用途，不证明原生 App 使用此主机。未登录、安装客户端或采集流量。

## 作用与边界

覆盖同主机所有路径，包括客户端下载入口与 WAP 营业厅；不另纳入独立官网、登录、商城、139 邮箱、其他运营商或原生客户端接口。未测试登录、实际下载或业务办理。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型中的首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增独立选择，不代表之前完全未覆盖。安全与游戏规则优先，此项在既有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`10086.cn`、`www.10086.cn`、`shop.10086.cn`、`login.10086.cn`、`h.app.coc.10086.cn`、`app.10086.cn`、`mail.10086.cn`、`www.10010.com`、`www.189.cn`保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `wap.10086.cn` gets a dedicated DIRECT-first selector for China Mobile. All paths on that host are covered; other hosts keep their existing routing. This is not a full native-app ruleset; native-client and live-network behavior were not tested.
