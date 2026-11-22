# 西瓜视频公开入口分流依据

基线：`c68ab146f974defd7ae05279956be8325b28222d`。新增 `DOMAIN,m.ixigua.com`，对应 `🍉 西瓜视频` 策略组，默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [西瓜视频官方下载页](https://m.ixigua.com/app_download)：同一主机介绍内容和客户端获取入口。
- [西瓜视频移动官网](https://m.ixigua.com/)：公开移动页面提供打开西瓜视频客户端的入口。
- [西瓜视频官方公开移动分享页](https://m.ixigua.com/dx/7678941464194272947)：同主机移动视频页面提供打开 App 的入口，图片来自不同主机。

证据级别：第一方网页或开发者公开资料，支持主机归属与公开入口用途，不代表真实原生客户端覆盖。只核对公开内容，不登录、不安装客户端、不采集流量。

## 作用与边界

同主机所有路径（含移动视频页面、分享与下载介绍）均随组；不另纳入桌面主站、创作平台、账号或共享字节素材主机，未验证原生接口和媒体传输。 规则按主机匹配，不按 URL 路径或发起进程匹配。不同主机仍可走不同出口。

基线离线域名模型中的原首匹配是 `ChinaMax → 🇨🇳 China-Global`。新增提供独立选择，不代表之前完全未覆盖。安全与游戏规则优先，新增项在已有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`ixigua.com`、`www.ixigua.com`、`studio.ixigua.com`、`live.ixigua.com`、`p3.bdxiguaimg.com`、`www.douyin.com`、`reading.snssdk.com` 一律保持原策略。另测子域、相似标签和伪装后缀。

## English scope

Only `m.ixigua.com` gets a dedicated DIRECT-first selector for Xigua Video. All paths on that host are covered; other hosts keep their existing routes. Native-client and live-network behavior were not tested.
