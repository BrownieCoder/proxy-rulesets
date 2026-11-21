# 番茄小说公开入口分流依据

基线：`70ae1f46dc8f9bb5a8a3a2709c9db8fe23333631`。新增 `DOMAIN,fanqienovel.com`，使用独立的 `🍅 番茄小说` 策略组：默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [番茄小说官网链接页](https://fanqienovel.com/friend_links)：把番茄小说 App 下载指向同一精确主机。
- [官方下载页](https://fanqienovel.com/app_download)：同主机提供 App 下载入口；安装文件主机不据此纳入。
- [番茄作家专区文章](https://fanqienovel.com/writer/zone/article/7638526211550871576)：同主机也承载创作者网页，部分登录或注册流程从该主机开始；不据此推断后续认证域名。

证据级别：第一方网页或开发者公开资料，足以说明主机归属和官网、网页阅读及 App 下载入口，不等于实测原生客户端。核对使用公开页面，不登录、下载 App 或采集流量。

## 作用与边界

同主机所有路径（含作家专区、帮助及该主机上的登录或注册网页）随组；不另纳入独立认证、其他阅读站、共享字节域名或 CDN，未验证完整登录、原生阅读或音频链路。 此规则按主机匹配，不按 URL 路径或发起进程匹配。其他主机可走不同出口。

在基线的离线有序域名模型中，此主机原先首先命中 `ChinaMax → 🇨🇳 China-Global`。新增是提供独立选项，不代表此前没有通用覆盖。顺序位于现有 App 之后、SiriAI 和通用规则之前；保留安全与游戏优先及末尾 MATCH。离线结果不代表 DNS、GeoIP、UDP 或真实 App 行为。

保持原策略的对照：`www.fanqienovel.com`、`www.changdunovel.com`、`reading.snssdk.com`、`lf-organic-growth.bytecdn.cn`、`www.douyin.com`，另含子域、相似标签和规避误匹配的后缀对照。

## English scope

Only `fanqienovel.com` gets a dedicated DIRECT-first selector for Fanqie Novel. This covers all paths on that host, not all traffic from the app. Other hosts keep their existing routes; native-client and real-network behavior were not tested.
