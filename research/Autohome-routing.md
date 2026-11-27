# 汽车之家：公开入口分流依据

基线：`890048c57acf673839e8f20175f9cd9686a27569`。新增 `DOMAIN,www.autohome.com.cn`，对应 `🚗 汽车之家` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [汽车之家官网](https://www.autohome.com.cn/)：公开首页实际链接到同主机的选车 `/price`、图库 `/cars/imglist`、排行榜 `/rank/1` 与文章 `/all/`。
- [中国区 App Store](https://apps.apple.com/cn/app/id385919493)：确认汽车之家 App 和 Autohome 开发者；开发者网站链接指向 `www.autohome.com.cn/apps/1.html`，隐私政策使用别域 `comm.app.autohome.com.cn`。
- [App Store 所列开发者网站入口](https://www.autohome.com.cn/apps/1.html)：本轮匿名读取发现跳转到 `www.athmapp.com/apps/main/`，目的地主机不纳入，也未触发下载。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未登录、安装客户端或采集流量。

## 作用与边界

同主机所有路径（含选车、资讯、图库和 App 介绍入口）均随组。跳转后的 App 下载站、独立账号与隐私页、报价接口、论坛或直播的另域以及共享图片域不另纳入。未验证安装、登录、询价、经销商或交易链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；跳转到别的主机会按新主机重新匹配，不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`autohome.com.cn`、`m.autohome.com.cn`、`www.athmapp.com`、`account.autohome.com.cn`、`comm.app.autohome.com.cn`、`sou.api.autohome.com.cn`、`z.autoimg.cn`、`al.autohome.com.cn`、`live.autohome.com.cn`、`www.dongchedi.com`、`www.yiche.com`、`www.che168.com` 保持原有策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.autohome.com.cn` gets a dedicated DIRECT-first selector. All paths on this hostname follow the selector; the App Store website link redirects to a different host that is not included. Existing privacy protections, Dongchedi routing, account and media hosts are unaffected by this rule. Native-app, installation, and transaction flows were not tested.
