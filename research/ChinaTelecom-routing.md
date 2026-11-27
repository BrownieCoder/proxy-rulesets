# 中国电信：公开入口分流依据

基线：`890048c57acf673839e8f20175f9cd9686a27569`。新增 `DOMAIN,www.189.cn`，对应 `📱 中国电信` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [中国电信集团客户服务联系方式](https://www.chinatelecom.com.cn/ct/xxgk/qylxfs/khfwlxfs/)：集团分别列出 `www.189.cn` 网上营业厅和中国电信掌上营业厅客户端。
- [中国区 App Store](https://apps.apple.com/cn/app/id513836029)：中国电信股份有限公司 App 的开发者网站和隐私政策均指向 `www.189.cn`。
- [中国电信网上营业厅的云南专区](https://www.189.cn/yn/mall/)：公开索引可见网上营业厅品牌和中国电信 App 下载二维码。当前匿名打开返回 HTTP 412；未验证下载或办理链路。
- [中国电信集团联系页](https://www.chinatelecom.com.cn/about/03/index.html)：确认全国网上营业厅及另域 `manyou.189.cn` 的国际漫游服务入口。
- [中国电信拖欠企业账款登记（投诉）平台使用说明（PDF）](https://www.189.cn/js/jsfile/20250862368f15852d46778b6d3dcb4cfb9273.pdf)：文件位于 `www.189.cn`，对该地址的请求随中国电信策略组。文件列出的实际登记平台在 `chinatelecomtsdj.bestpay.com.cn`，不随组；未登录或提交登记。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未登录、安装客户端或采集流量。

## 作用与边界

同主机的所有网页路径（含各省放在此主机上的专区和 App 商店列出的隐私页）均随组；另域的省级网厅、国际漫游服务、集团网站、认证、支付和原生接口不另纳入。未验证安装、登录、充值、订单或业务办理链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；跳转到别的主机会按新主机重新匹配，不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`189.cn`、`gd.189.cn`、`m.gd.189.cn`、`sh.189.cn`、`manyou.189.cn`、`www.chinatelecom.com.cn`、`www.10086.cn`、`www.10010.com`、`www.95598.cn`、`chinatelecomtsdj.bestpay.com.cn` 保持原有策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.189.cn` gets this DIRECT-first selector. All paths on the hostname follow it, including provincial pages and the App Store privacy link there. Separate regional portals, roaming, corporate, authentication, and payment hosts retain their existing routing. This does not validate native-app traffic or transaction flows.

The public arrears complaint guide on `www.189.cn` follows this selector; its separate filing host `chinatelecomtsdj.bestpay.com.cn` keeps the existing route. Filing was not tested.
