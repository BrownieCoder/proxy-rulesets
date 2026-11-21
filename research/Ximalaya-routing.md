# 喜马拉雅公开入口分流依据

基线：`70ae1f46dc8f9bb5a8a3a2709c9db8fe23333631`。新增 `DOMAIN,m.ximalaya.com`，使用独立的 `🎧 喜马拉雅` 策略组：默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [官方主播帮助中心](https://www.ximalaya.com/helper/questionPage?questionId=617)：说明 App 内复制得到的分享链接使用此主机。
- [喜马拉雅移动电台](https://m.ximalaya.com/radio/)：同主机承载公开移动电台目录。

证据级别：第一方网页或开发者公开资料，足以说明主机归属和移动网页、电台目录及 App 分享入口，不等于实测原生客户端。核对使用公开页面，不登录、下载 App 或采集流量。

## 作用与边界

同主机所有路径（含公开分享和会员介绍网页）随组；不同主机的音频、登录、主播工作台、开放平台与海外版不纳入。 此规则按主机匹配，不按 URL 路径或发起进程匹配。其他主机可走不同出口。

在基线的离线有序域名模型中，此主机原先首先命中 `ChinaMax → 🇨🇳 China-Global`。新增是提供独立选项，不代表此前没有通用覆盖。顺序位于现有 App 之后、SiriAI 和通用规则之前；保留安全与游戏优先及末尾 MATCH。离线结果不代表 DNS、GeoIP、UDP 或真实 App 行为。

保持原策略的对照：`ximalaya.com`、`www.ximalaya.com`、`passport.ximalaya.com`、`live.ximalaya.com`、`studio.ximalaya.com`、`open.ximalaya.com`、`everest-ai.ximalaya.com`，另含子域、相似标签和规避误匹配的后缀对照。

## English scope

Only `m.ximalaya.com` gets a dedicated DIRECT-first selector for Ximalaya. This covers all paths on that host, not all traffic from the app. Other hosts keep their existing routes; native-client and real-network behavior were not tested.
