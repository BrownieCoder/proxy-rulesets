# 小宇宙公开入口分流依据

基线：`31d0baa1da42d02d9b97d6399ad4fc3a4bf1a40b`。新增 `DOMAIN,www.xiaoyuzhoufm.com`，对应 `🎙️ 小宇宙` 策略组，默认直连（DIRECT），可手动选择节点或 Final。

## 官方依据

- [小宇宙官网](https://www.xiaoyuzhoufm.com/)：列出听播客与体验入口。
- [小宇宙公开单集页](https://www.xiaoyuzhoufm.com/episode/69ac329bc8cdeb38c25497d4)：单集页也在该主机，封面由另域提供。
- [中国 App Store](https://apps.apple.com/cn/app/id1488894313)：确认客户端和开发者，不证明客户端调用该主机。

证据级别：第一方公开网页或开发者在应用商店提供的资料。证据支持主机归属及公开入口用途，不证明原生 App 使用此主机。未登录、安装客户端或采集流量。

## 作用与边界

覆盖同主机的官网、节目和单集网页；不另纳入播客工作台、官方博客、条款子域、封面 CDN、音频传输或原生客户端接口。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型中的首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增独立选择，不代表之前完全未覆盖。安全与游戏规则优先，此项在既有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`xiaoyuzhoufm.com`、`blog.xiaoyuzhoufm.com`、`studio.xiaoyuzhoufm.com`、`static.xiaoyuzhoufm.com`、`post.xiaoyuzhoufm.com`、`image.xyzcdn.net`、`post.jellow.club`、`m.ximalaya.com`、`www.lizhi.fm`保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.xiaoyuzhoufm.com` gets a dedicated DIRECT-first selector for Xiaoyuzhou. All paths on that host are covered; other hosts keep their existing routing. This is not a full native-app ruleset; native-client and live-network behavior were not tested.
