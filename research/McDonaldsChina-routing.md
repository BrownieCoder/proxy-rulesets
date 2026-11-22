# 麦当劳中国公开入口分流依据

基线：`c68ab146f974defd7ae05279956be8325b28222d`。新增 `DOMAIN,www.mcdonalds.com.cn`，对应 `🍔 麦当劳中国` 策略组，默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [麦当劳中国官网的移动服务介绍](https://www.mcdonalds.com.cn/index/Services/anytime-anywhere)：同主机介绍官方 App 并提供下载入口。
- [麦当劳中国官方声明](https://www.mcdonalds.com.cn/index/mcd/disclosure/public-statement)：分别明确官网和官方 App 的身份。
- [中国 App Store](https://apps.apple.com/cn/app/id1054598922)：确认官方中国区 App；开发者隐私链接使用不同主机。

证据级别：第一方网页或开发者公开资料，支持主机归属与公开入口用途，不代表真实原生客户端覆盖。只核对公开内容，不登录、不安装客户端、不采集流量。

## 作用与边界

同主机所有路径（包括菜单、营销活动和下载介绍网页）均随组；不另纳入全球站、独立点餐、登录、支付、隐私说明或媒体主机，未验证原生客户端业务链路。 规则按主机匹配，不按 URL 路径或发起进程匹配。不同主机仍可走不同出口。

基线离线域名模型中的原首匹配是 `ChinaMax → 🇨🇳 China-Global`。新增提供独立选择，不代表之前完全未覆盖。安全与游戏规则优先，新增项在已有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`mcdonalds.com.cn`、`www.mcdonalds.com`、`www.mcd.cn`、`www.4008-517-517.cn`、`www.kfc.com.cn` 一律保持原策略。另测子域、相似标签和伪装后缀。

## English scope

Only `www.mcdonalds.com.cn` gets a dedicated DIRECT-first selector for McDonald’s China. All paths on that host are covered; other hosts keep their existing routes. Native-client and live-network behavior were not tested.
