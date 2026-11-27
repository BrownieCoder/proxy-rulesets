# 贝壳找房：公开入口分流依据

基线：`890048c57acf673839e8f20175f9cd9686a27569`。新增 `DOMAIN,www.ke.com`，对应 `🏠 贝壳找房` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [贝壳官方 App 下载介绍](https://www.ke.com/client)：公开页面展示贝壳 App 及扫码入口，二维码和图片分别引用 `ajax.api.ke.com`、`file.ljcdn.com`、`img.ljcdn.com` 等别域，未触发下载。
- [贝壳内容创作用户服务协议](https://www.ke.com/zhuanti/commonProtocol?id=21)：明确平台包括 `www.ke.com` 网站、`m.ke.com` 和 `wap.ke.com` 等移动站及 App；此次只纳入前者。
- [贝壳官网](https://www.ke.com/)：本轮匿名访问跳转至 `bj.ke.com`，本规则不改变该北京站的路由，不推断其他访问者的跳转目的地。
- [中国区 App Store](https://apps.apple.com/cn/app/id1347663353)：确认贝壳 App 和发行方；隐私政策链接位于 `www.ke.com`，开发者网站栏目指向别域 `bkzhibo.com`，不另纳入。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未登录、安装客户端或采集流量。

## 作用与边界

同主机所有路径（含下载介绍和协议页）均随组。本轮官网根路径跳转到北京站；北京、上海等别域城市站、移动站、下载页的二维码或素材域不随组。未验证安装、登录、房源完整浏览、预约或交易链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；跳转到别的主机会按新主机重新匹配，不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`ke.com`、`bj.ke.com`、`sh.ke.com`、`m.ke.com`、`wap.ke.com`、`map.ke.com`、`ajax.api.ke.com`、`file.ljcdn.com`、`img.ljcdn.com`、`bkzhibo.com`、`www.lianjia.com`、`www.anjuke.com`、`www.fang.com` 保持原有策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.ke.com` gets a dedicated DIRECT-first selector. All requests to that hostname, including the download information and agreement pages, follow it. City-site redirects, mobile websites, QR-code and asset hosts are matched independently; no native-app, sign-in, reservations, or transaction coverage was validated.
