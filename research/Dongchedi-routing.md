# 懂车帝公开入口分流依据

基线：`c594b80a278cc48e4e363747a9627d8b2bae29be`。新增 `DOMAIN,www.dongchedi.com`，对应 `🚘 懂车帝` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [懂车帝官网](https://www.dongchedi.com/)：公开页面展示懂车帝品牌与汽车内容。
- [懂车帝官方下载介绍](https://www.dongchedi.com/download/)：同一主机提供懂车帝 App 的下载介绍，页面的图片和下载二维码引用另域 `lf3-motor.dcarstatic.com`；未触发下载。
- [中国区 App Store](https://apps.apple.com/cn/app/id1232131998)：确认懂车帝 App 及发行方身份；不能据此认定原生调用或 CDN 范围。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未安装客户端、登录或采集流量。

## 作用与边界

同主机所有路径均随组；独立 App 服务域、共享 CDN、登录、询价和交易接口不另纳入。未验证安装、登录或原生 App 链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：下载页素材域 `lf3-motor.dcarstatic.com` 不随组，离线首匹配仍为 `ChinaMax → 🇨🇳 China-Global`。`dongchedi.com`、`m.dongchedi.com`、`dcdapp.com`、`dongchediapp.com`、`lf3-cdn-tos.draftstatic.com`、`api.dcarapi.com`、`www.autohome.com.cn`、`www.yiche.com`、`www.douyin.com`、`example.org` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.dongchedi.com` gets a dedicated DIRECT-first selector for Dongchedi. All paths on that hostname follow the selector, while the download page's separate image and QR-code host `lf3-motor.dcarstatic.com` keeps its existing route. This is not full native-app coverage; live network and client behavior were not tested.
