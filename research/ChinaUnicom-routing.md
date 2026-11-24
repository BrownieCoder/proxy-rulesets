# 中国联通公开入口分流依据

基线：`131354c31397a4105cd6944c13aea5f81315eeaf`。新增 `DOMAIN,wap.10010.com`，对应 `📶 中国联通` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [联通移动营业厅](https://wap.10010.com/mobileService/waphome.htm)：移动营业厅主页和客户端入口；余量查询、电子发票等图标由另域 `m1.img.10010.com` 提供。
- [联通渠道说明](https://wap.10010.com/t/query/queryTranster.htm?listType=aboutUs)：将移动电子渠道与电脑网上营业厅区分。
- [中国区 App Store](https://apps.apple.com/cn/app/id416457422)：确认官方发行方。

证据级别：第一方公开网页或应用商店开发者资料，支持主机归属与公开用途，不证明原生客户端调用该主机。未登录、安装客户端或采集流量。

## 作用与边界

同主机所有路径（含 WAP 营业厅及其业务页面）均随组；电脑版官网、独立认证、商城、介绍页、素材及其他运营商保持原策略，未实测登录、实际下载或业务办理。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。安全与游戏仍优先，此项位于既有 App 之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`10010.com`、`www.10010.com`、`m.10010.com`、`mall.10010.com`、`m.client.10010.com`、`uac.10010.com`、`img.client.10010.com`、`m1.img.10010.com`、`res.mall.10010.cn`、`www.chinaunicom.com`、`wap.10086.cn`、`www.189.cn` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `wap.10010.com` gets a dedicated DIRECT-first selector for China Unicom. All paths on that hostname follow the selector; other hosts keep their existing routes. This is not full native-app coverage; live network and client behavior were not tested.
