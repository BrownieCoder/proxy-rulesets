# 央视频公开入口分流依据

基线：`c594b80a278cc48e4e363747a9627d8b2bae29be`。新增 `DOMAIN,www.yangshipin.cn`，对应 `🎞️ 央视频` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [央视频官网](https://www.yangshipin.cn/index.html)：同主机公开页展示央视频 App 下载二维码及节目入口；未验证安装或播放。
- [中国区 App Store](https://apps.apple.com/cn/app/id1479814602)：确认央视频 App；其会员相关协议链接使用独立 `m.yangshipin.cn`，不另纳入。
- [央视频用户协议](https://passport.yangshipin.cn/html/user_agreement.html)：说明中央广播电视总台运营央视频，区分网站和客户端；协议所在认证主机不另纳入。
- [央视频号](https://mp.yangshipin.cn/)与[创作者平台服务协议](https://mpstatic.ysp.cctv.cn/mp/mp_style/files/xieyi.htm)：创作者平台入口与协议网页均使用不同于官网的主机，不纳入专属策略。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未安装客户端、登录或采集流量。

## 作用与边界

同主机所有路径均随组；独立登录、会员协议、央视其他服务与播放 CDN 不另纳入。未验证原生 App、安装、登录、会员或播放链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：央视频号 `mp.yangshipin.cn` 与创作者平台协议主机 `mpstatic.ysp.cctv.cn` 不随组，离线首匹配均仍为 `ChinaMax → 🇨🇳 China-Global`。`yangshipin.cn`、`m.yangshipin.cn`、`passport.yangshipin.cn`、`www.cctv.com`、`tv.cctv.com`、`news.cctv.com`、`www.cctv.cn`、`www.bilibili.com`、`example.org` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.yangshipin.cn` gets a dedicated DIRECT-first selector for Yangshipin. All paths on that hostname follow the selector. The creator portal `mp.yangshipin.cn` and its agreement host `mpstatic.ysp.cctv.cn` keep their existing routes. This is not full native-app coverage; live network and client behavior were not tested.
