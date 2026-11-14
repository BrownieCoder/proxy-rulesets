# 抖音官网与静态主机分流依据

## 决定

仅为本次官方页面可直接核实的三个精确主机提供 `🎶 抖音` 策略，默认 `DIRECT`，保留手动代理选择。
三个主机原本均由 ChinaMax 命中 `🇨🇳 China-Global`；此次价值是独立出口控制和先于通用服务的匹配位置，不是此前完全没有覆盖。

## 公开证据

采集日期：2026-11-14。无登录读取[抖音官方下载页面](https://www.douyin.com/downloadpage/pc)，区分实际 HTML 标签引用与脚本白名单中的候选项。只保留主机名，不保存页面中的用户内容或带参数链接。

| 精确主机 | 官方来源与观察 | 用途 / 目标 | 置信度与范围 |
| --- | --- | --- | --- |
| `www.douyin.com` | 官方下载页本身，及页面中回到抖音官网的链接 | 官网和下载入口；默认直连 | 高；仅本主机 |
| `lf-douyin-pc-web.douyinstatic.com` | 同一官方 HTML 中的实际 `script src` 与样式资源引用 | 抖音网页静态资源；默认直连 | 高；仅本主机，不扩展 `douyinstatic.com` |
| `sf1-cdn-tos.douyinstatic.com` | 同一官方 HTML 中的实际 `script src` 引用 | 抖音网页脚本资源；默认直连 | 高；仅本主机，不推断整个 CDN 的用途 |

置信度只表示官网实际使用该主机的证据，不代表所有权审计、原生 App 覆盖或各地区可达性保证。未纳入共享字节根域、其他视频平台、TikTok 或其 CDN。

## 未纳入的候选

上述 HTML 还有 `v3-web.douyinvod.com`、`v26-web.douyinvod.com`、`v11-web-prime.douyinvod.com`、`v26-web-prime.douyinvod.com`、`v95-web-sz.douyinvod.com` 的 `link rel="dns-prefetch"` 提示。
DNS 预取提示不足以证明实际视频播放链路，本次仅记录为候选，不进入正式规则。其他脚本白名单项也不能直接当成已观察请求。

## 路由边界

保留 Privacy、Hijacking 与游戏优先；本组在通用 Apple、TikTok、国际媒体、GeoIP 中国和 ChinaMax 之前。安全规则后来若加入这些主机，合法的安全策略仍先匹配。

手动把 `🎶 抖音` 切到代理只影响这三个主机；其他抖音图片、视频、API、直播或登录主机继续使用原有规则，可能仍直连，因而可能混合出口。本组不保证原生 App 全链路、播放、直播、账户登录或一致出口 IP。

离线检查证明精确范围、实际域名首匹配、安全优先、默认值与代理选项，并验证 TikTok 对照和相似域名不改变路由。没有读取私人配置或登录账号，没有采集私人流量，也未执行带账户 App、视频播放、DNS/GeoIP 或 UDP 实测。
