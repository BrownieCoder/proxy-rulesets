# 唯品会公开入口分流依据

基线：`c68ab146f974defd7ae05279956be8325b28222d`。新增 `DOMAIN,www.vip.com`，对应 `🛍️ 唯品会` 策略组，默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [唯品会官方业务范围](https://sec.vip.com/vip)：分列消费者 App、唯品会主站、VIPSHOP 及唯品支付，明确该主站的精确主机。
- [中国 App Store](https://apps.apple.com/cn/app/id417200582)：确认消费者 App；不据此推断 App 使用主站的网络链路。

证据级别：第一方网页或开发者公开资料，支持主机归属与公开入口用途，不代表真实原生客户端覆盖。只核对公开内容，不登录、不安装客户端、不采集流量。

## 作用与边界

同主机所有路径均随组；官网与 App 是同一消费服务的不同入口。未验证 App 会访问此主机，不另纳入移动站、独立帮助或登录、商家平台、唯品支付、国际站和 CDN。 规则按主机匹配，不按 URL 路径或发起进程匹配。不同主机仍可走不同出口。

基线离线域名模型中的原首匹配是 `ChinaMax → 🇨🇳 China-Global`。新增提供独立选择，不代表之前完全未覆盖。安全与游戏规则优先，新增项在已有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`vip.com`、`m.vip.com`、`help.vip.com`、`myi.vip.com`、`vis.vip.com`、`www.vipshop.com`、`www.vpal.com`、`a.vpimg2.com`、`mst.vip.com` 一律保持原策略。另测子域、相似标签和伪装后缀。

## English scope

Only `www.vip.com` gets a dedicated DIRECT-first selector for Vipshop. All paths on that host are covered; other hosts keep their existing routes. Native-client and live-network behavior were not tested.
