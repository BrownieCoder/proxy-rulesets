# 肯德基中国公开入口分流依据

基线：`70ae1f46dc8f9bb5a8a3a2709c9db8fe23333631`。新增 `DOMAIN,www.kfc.com.cn`，使用独立的 `🍗 肯德基中国` 策略组：默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [肯德基中国官方下载页](https://www.kfc.com.cn/app/index.html)：同主机介绍肯德基 App，并提供下载二维码。
- [中国 App Store](https://apps.apple.com/cn/app/id587238847)：开发者页面确认中国区肯德基 App，并把同一主机列为开发者网站；隐私说明是另一个主机。

证据级别：第一方网页或开发者公开资料，足以说明主机归属和中国官网和同主机 App 下载介绍页，不等于实测原生客户端。核对使用公开页面，不登录、下载 App 或采集流量。

## 作用与边界

同主机所有路径（含品牌、活动及下载介绍网页）随组；不纳入独立订餐、登录、支付、素材或全球站主机。 此规则按主机匹配，不按 URL 路径或发起进程匹配。其他主机可走不同出口。

在基线的离线有序域名模型中，此主机原先首先命中 `ChinaMax → 🇨🇳 China-Global`。新增是提供独立选项，不代表此前没有通用覆盖。顺序位于现有 App 之后、SiriAI 和通用规则之前；保留安全与游戏优先及末尾 MATCH。离线结果不代表 DNS、GeoIP、UDP 或真实 App 行为。

保持原策略的对照：`kfc.com.cn`、`www.kfc.com`、`www.yumchina.com`、`www.4008823823.com.cn`、`www.mcdonalds.com.cn`、`appcommon.kfc.com.cn`，另含子域、相似标签和规避误匹配的后缀对照。

## English scope

Only `www.kfc.com.cn` gets a dedicated DIRECT-first selector for KFC China. This covers all paths on that host, not all traffic from the app. Other hosts keep their existing routes; native-client and real-network behavior were not tested.
