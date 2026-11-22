# 虎牙直播公开入口分流依据

基线：`c68ab146f974defd7ae05279956be8325b28222d`。新增 `DOMAIN,hd.huya.com`，对应 `🐯 虎牙直播` 策略组，默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [虎牙官方客户端中心](https://hd.huya.com/appdownload/)：同主机介绍移动客户端下载；其中安装包链接使用不同主机。
- [虎牙开放平台文档](https://hd.huya.com/h5/hy-open-doc/miniapp/dev/framework/host/pc/)：同主机还承载开放平台文档，按主机匹配会一并影响。
- [中国 App Store](https://apps.apple.com/cn/app/id871095743)：确认官方虎牙直播 App，不证明原生 App 访问此主机。

证据级别：第一方网页或开发者公开资料，支持主机归属与公开入口用途，不代表真实原生客户端覆盖。只核对公开内容，不登录、不安装客户端、不采集流量。

## 作用与边界

同主机所有路径（包括营销活动、客户端下载介绍和开放平台网页）均随组；不另纳入直播主站、登录、原生接口、不同主机的安装包、媒体传输或 CDN。 规则按主机匹配，不按 URL 路径或发起进程匹配。不同主机仍可走不同出口。

基线离线域名模型中的原首匹配是 `ChinaMax → 🇨🇳 China-Global`。新增提供独立选择，不代表之前完全未覆盖。安全与游戏规则优先，新增项在已有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`huya.com`、`www.huya.com`、`m.huya.com`、`api.m.huya.com`、`app-agreements.huya.com`、`dev.huya.com`、`rel.huya.com`、`metric.huya.com` 一律保持原策略。另测子域、相似标签和伪装后缀。

## English scope

Only `hd.huya.com` gets a dedicated DIRECT-first selector for Huya Live. All paths on that host are covered; other hosts keep their existing routes. Native-client and live-network behavior were not tested.
