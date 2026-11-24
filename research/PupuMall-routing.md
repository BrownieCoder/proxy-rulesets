# 朴朴超市公开入口分流依据

基线：`131354c31397a4105cd6944c13aea5f81315eeaf`。新增 `DOMAIN,www.pupumall.com`，对应 `🛒 朴朴超市` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [朴朴超市官方首页](https://www.pupumall.com/)：介绍即时零售平台并列出 App 下载项；未实际下载。
- [中国区 App Store](https://apps.apple.com/cn/app/id1144025167)：确认消费者 App 与开发者；列出的隐私政策使用另域。

证据级别：第一方公开网页或应用商店开发者资料，支持主机归属与公开用途，不证明原生客户端调用该主机。未登录、安装客户端或采集流量。

## 作用与边界

同主机所有路径（含企业和平台介绍）均随组；独立隐私站、原生 API、订单和支付主机不另纳入，未实测下载、登录、下单或支付。叮咚和盒马的既有策略保留。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。安全与游戏仍优先，此项位于既有 App 之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`pupumall.com`、`pupumall.net`、`www.pupumall.net`、`c.pupuapi.com`、`ma.pupumall.com`、`www.100.me`、`maicai.api.ddxq.mobi`、`www.freshippo.com` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.pupumall.com` gets a dedicated DIRECT-first selector for Pupu Mall. All paths on that hostname follow the selector; other hosts keep their existing routes. This is not full native-app coverage; live network and client behavior were not tested.
