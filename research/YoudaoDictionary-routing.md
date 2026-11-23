# 网易有道词典公开入口分流依据

基线：`31d0baa1da42d02d9b97d6399ad4fc3a4bf1a40b`。新增 `DOMAIN,dict.youdao.com`，对应 `📖 网易有道词典` 策略组，默认直连（DIRECT），可手动选择节点或 Final。

## 官方依据

- [网易有道词典公开词条](https://dict.youdao.com/w/eng/computer/)：证明网页查词功能；页面另链到独立翻译、课程、云笔记与账号主机。
- [网易有道词典首页](https://dict.youdao.com/)：首页引用 `ydlunacommon-cdn.nosdn.127.net` 和 `luna-dict-community.nosdn.127.net` 上的图片；两者均为另域，不随词典策略组切换。
- [网易有道词典服务条款](https://c.youdao.com/dict/law/youdao_dict_service.html)：区分网站、App、桌面端和小程序。
- [中国 App Store](https://apps.apple.com/cn/app/id353115739)：确认官方网易有道词典客户端。

证据级别：第一方公开网页或开发者在应用商店提供的资料。证据支持主机归属及公开入口用途，不证明原生 App 使用此主机。未登录、安装客户端或采集流量。

## 作用与边界

覆盖该主机所有路径（含主页、词条和同主机翻译入口）；不另纳入独立翻译和桌面版下载主机、登录、课程、云笔记、隐私跟踪、共享素材或网易邮箱。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型中的首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增独立选择，不代表之前完全未覆盖。安全与游戏规则优先，此项在既有 App 之后、SiriAI 及通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或实际 App 行为。

对照：`youdao.com`、`www.youdao.com`、`fanyi.youdao.com`、`cidian.youdao.com`、`account.youdao.com`、`ke.youdao.com`、`note.youdao.com`、`ydlunacommon.nosdn.127.net`、`ydlunacommon-cdn.nosdn.127.net`、`luna-dict-community.nosdn.127.net`、`rlogs.youdao.com`、`mail.163.com` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `dict.youdao.com` gets a dedicated DIRECT-first selector for Youdao Dictionary. All paths on that host are covered; other hosts keep their existing routing. This is not a full native-app ruleset; native-client and live-network behavior were not tested.
