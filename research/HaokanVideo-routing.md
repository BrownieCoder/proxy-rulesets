# 好看视频公开入口分流依据

基线：`131354c31397a4105cd6944c13aea5f81315eeaf`。新增 `DOMAIN,haokan.baidu.com`，对应 `🎬 好看视频` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [好看视频首页](https://haokan.baidu.com/)：页面引用 `mpics.bdstatic.com` 上的图片，并链接到另域 `live.baidu.com` 的百度直播；两者不随组。
- [好看视频官方下载介绍](https://haokan.baidu.com/download)：好看视频的官方公开下载页，页面引用另域图片。
- [好看视频官方协议](https://haokan.baidu.com/videoui/page/about)：明确区分网页端与移动等使用方式，不能据此认定原生客户端调用范围。
- [中国区 App Store](https://apps.apple.com/cn/app/%E5%A5%BD%E7%9C%8B%E8%A7%86%E9%A2%91/id1092031003?platform=ipad)：确认好看视频客户端及百度发行方。

证据级别：第一方公开网页或应用商店开发者资料，支持主机归属与公开用途，不证明原生客户端调用该主机。未登录、安装客户端或采集流量。

## 作用与边界

同主机所有路径（含网页版、下载介绍和协议页）均随组；百度搜索、账号、地图、百家号、独立素材、播放 CDN 和原生接口不另纳入。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。安全与游戏仍优先，此项位于既有 App 之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`baidu.com`、`www.baidu.com`、`m.baidu.com`、`map.baidu.com`、`passport.baidu.com`、`baijiahao.baidu.com`、`imgsa.baidu.com`、`mpics.bdstatic.com`、`live.baidu.com`、`mobile.baidu.com`、`image.baidu.com` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `haokan.baidu.com` gets a dedicated DIRECT-first selector for Haokan Video. All paths on that hostname follow the selector; other hosts keep their existing routes. This is not full native-app coverage; live network and client behavior were not tested.
