# 什么值得买：公开入口分流依据

基线：`890048c57acf673839e8f20175f9cd9686a27569`。新增 `DOMAIN,www.smzdm.com`，对应 `🏷️ 什么值得买` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [什么值得买官网](https://www.smzdm.com/)：公开首页展示消费指南及推荐内容，并链接到 `post.smzdm.com` 的社区文章和其他服务；只纳入 `www.smzdm.com`。
- [什么值得买用户协议](https://www.smzdm.com/user/register/provisions/)：区分 `www.smzdm.com` 网页、客户端和小程序等产品入口。
- [中国区 App Store](https://apps.apple.com/cn/app/id518213356)：确认什么值得买 App 和北京值得买科技；开发者网站栏目链接到官网，隐私政策链接在另域 `res.smzdm.com`。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未登录、安装客户端或采集流量。

## 作用与边界

同主机所有路径均随组，包括官网的好价、内容及协议入口。独立的社区文章、用户主页、移动协议或隐私页、素材域、商业合作及外部电商不另纳入。未验证安装、登录、下单或支付链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；跳转到别的主机会按新主机重新匹配，不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`smzdm.com`、`post.smzdm.com`、`zhiyou.smzdm.com`、`zhiyou.m.smzdm.com`、`res.smzdm.com`、`static.smzdm.com`、`qny.smzdm.com`、`y.zdmimg.com`、`e.smzdm.com` 保持原有策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.smzdm.com` gets a dedicated DIRECT-first selector. All paths on the hostname follow it. Separate community, profile, privacy, asset and merchant hosts are excluded and keep their existing routes. This does not validate native-app, sign-in, checkout, or payment flows.
