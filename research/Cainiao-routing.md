# 菜鸟公开入口分流依据

基线：`131354c31397a4105cd6944c13aea5f81315eeaf`。新增 `DOMAIN,newconnection.cainiao.com`，对应 `📦 菜鸟` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [菜鸟裹裹消费者入口](https://newconnection.cainiao.com/act/cnindexpc.html)：介绍收寄服务及 App 下载入口；使用另域共享图片。
- [菜鸟公开活动页](https://newconnection.cainiao.com/act/guoguo-qrj.html)：佐证同一主机也有活动页。
- [中国区 App Store](https://apps.apple.com/cn/app/id951610982)：确认消费者 App 和发行方。

证据级别：第一方公开网页或应用商店开发者资料，支持主机归属与公开用途，不证明原生客户端调用该主机。未登录、安装客户端或采集流量。

## 作用与边界

同主机所有路径（包括收寄介绍和活动页）均随组；集团站、独立隐私/商家页面、共享素材和其他快递服务不另纳入，未验证原生查件、登录和业务链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。安全与游戏仍优先，此项位于既有 App 之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`cainiao.com`、`www.cainiao.com`、`page.cainiao.com`、`img.alicdn.com`、`cainiaoyizhan.com`、`www.cainiao.com.cn`、`www.taobao.com`、`www.sf-express.com`、`www.zto.com` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `newconnection.cainiao.com` gets a dedicated DIRECT-first selector for Cainiao. All paths on that hostname follow the selector; other hosts keep their existing routes. This is not full native-app coverage; live network and client behavior were not tested.
