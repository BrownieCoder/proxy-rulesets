# Keep公开入口分流依据

基线：`31d0baa1da42d02d9b97d6399ad4fc3a4bf1a40b`。新增 `DOMAIN,www.calorietech.com`，对应 `🏃 Keep` 策略组，默认直连（DIRECT），可手动选择节点或 Final。

## 官方依据

- [Keep 中国官网](https://www.calorietech.com/)：北京卡路里科技的官网，包含产品、运动课程及企业页面。
- [Keep App 官方下载介绍](https://www.calorietech.com/app)：标明应用名和开发者；下载按钮跳至不同主机 gotokeep.com，图片来自独立 CDN。
- [中国 App Store](https://apps.apple.com/cn/app/id952694580)：独立核对中国版客户端与开发者。

证据级别：第一方公开网页或开发者在应用商店提供的资料。证据支持主机归属及公开入口用途，不证明原生 App 使用此主机。未登录、安装客户端或采集流量。

## 作用与边界

覆盖同主机所有路径（含 App 下载介绍、运动课程、消费品、硬件及企业公开网页）；下载跳转主机、国际商城、独立商城、政策或应用权限子域及 CDN 不另纳入。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型中的首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增独立选择，不代表之前完全未覆盖。安全与游戏规则优先，此项在既有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`calorietech.com`、`gotokeep.com`、`www.gotokeep.com`、`show.gotokeep.com`、`m.gotokeep.com`、`mo.gotokeep.com`、`static1.keepcdn.com`、`staticweb.keepcdn.com`、`keep.com`、`ir.keep.com`保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.calorietech.com` gets a dedicated DIRECT-first selector for Keep Fitness. All paths on that host are covered; other hosts keep their existing routing. This is not a full native-app ruleset; native-client and live-network behavior were not tested.
