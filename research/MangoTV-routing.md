# 芒果TV公开入口精确分流依据

核实日期：2026-11-21。范围仅为 `DOMAIN,www.mgtv.com`，新增 `MangoTV` provider 和 `🥭 芒果TV` 独立策略组；默认直连，可手动选代理或 Final。不是芒果TV客户端完整分流。

## 官方证据

| 精确主机 | 官方来源及观察 | 能证明什么 |
| --- | --- | --- |
| `www.mgtv.com` | [运营方业务构成](https://corp.mgtv.com/product/)标注该主机为芒果TV PC 站，并将移动 App、PC 客户端和国际业务另列。[官网](https://www.mgtv.com/)展示芒果TV标识和客户端入口。 | 高置信：官方公开 PC 门户；官网声明不等于原生客户端网络行为实测。 |
| 同一主机，不增加域名 | [中国 App Store 芒果TV](https://apps.apple.com/cn/app/id629774477)的开发者网站指向该主机，点击读到同主机的[客户端介绍页](https://www.mgtv.com/app/)。[另一公开客户端页](https://www.mgtv.com/app/index.html)列出 Android、iPhone、iPad 和桌面版，并链接到独立下载主机。 | 高置信：同主机官方产品介绍的公开页面；未跟随下载链接，不把安装包服务或客户端流量归给官网。 |

这里使用网页工具的匿名读取及开发者公开声明，部分结果为缓存；不把它们描述为实时 HTTP 测量。未登录、购买、播放、下载、执行页面脚本或采集私人流量。

## 国际版、其他主机及同主机路径

- [国际版服务条款](https://www.mgtv.com/general_agreement/c_protocol_en.html)把 `w.mgtv.com` 声明为国际服务网站；[国际门户](https://w.mgtv.com/)本身不纳入。条款文件却发布在 `www.mgtv.com`，且[美国 App Store 的 MangoTV](https://apps.apple.com/us/app/mangotv/id1295034410)的开发者网站也返回 `www.mgtv.com/app/`。规则按主机而非路径或市场划分：国际版如果访问这一个主机，也会使用本组，不能称国际版全部流量不受影响。
- `mgtv.com` 根域、`corp.mgtv.com`、`club.mgtv.com`、`order.mgtv.com`、`app.mgtv.com`、`i.mgtv.com`、`img.mgtv.com`、`7.mgtv.com` 及其他子域仍由原规则处理。不切换公司、交易、创作、图片、登录或独立服务流量。
- 客户端页有指向 `download.hitv.com`、`download.imgo.tv`、`download.hunantv.com` 及应用商店的链接，介绍/下载页面也声明了 `ugc.hitv.com` 和 `ossimg.hitv.com` 的图片。未请求这些安装包或资源；不纳入整根域、共享资源、广告/日志、播放 CDN 或未经验证的 API。
- 精确匹配会接管 `www.mgtv.com` 全部路径，其他请求仍可能使用不同出口。即使切换代理，也不能保证页面加载、原生 App、下载、登录、购买、会员或视频播放，更不改变版权、账号或地区资格。

## 当前首匹配与验证约束

基线 `9b0a5eb64c9a241b1bcd049c8526af7c97768571`。目录和本地清单没有独立芒果TV规则；基于公开模板顺序和快照的实际离线模拟中，`www.mgtv.com` 原为 `ChinaMax → 🇨🇳 China-Global`，新增价值是独立出口，并非此前未覆盖。

| 对象 | 基线首匹配 |
| --- | --- |
| `www.mgtv.com`、`w.mgtv.com`、`mgtv.com`、`corp.mgtv.com`、`app.mgtv.com`、`img.mgtv.com`、`club.mgtv.com`、`7.mgtv.com` | `ChinaMax → 🇨🇳 China-Global` |
| `log.mgtv.com`（现有快照对照，非网站请求观测） | `Privacy → REJECT` |
| `www.iqiyi.com`、`www.youku.com`、`v.qq.com`、`www.bilibili.com` | 分别沿爱奇艺、优酷、腾讯视频及 Bilibili 原规则 |
| `game.qq.com`、`guzzoni.apple.com`、`example.org` | 分别沿 ChinaGaming、SiriAI、MATCH 原规则 |

唯一活动引用放在全部既有 App 之后、SiriAI 及通用媒体/地区规则之前；安全、游戏与既有例外仍优先。门禁验证固定精确域、唯一引用、顺序、策略组选项和真实模板首匹配；允许合法 Privacy 拦截或 Hijacking 优先。非安全抢先、未知 provider、缺失字段或前置 IP 条件须拒绝。排除主机、现有服务及相似子域/后缀的匹配结果不得改变。这里只模拟域名输入，不替代 DNS、GeoIP、UDP 或真实代理测试。

[Mihomo 固定版本](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L34)的域规则构造会将操作数转成小写；本门禁对明文字段及 provider 的 ASCII 域规则操作数做同样比较，防止大写规则抢先却被离线模型漏报。无关模板、规则和共享模型不改。

## English scope summary

One exact host, `www.mgtv.com` (official portal and same-host client introduction), gets a DIRECT-first select group with optional manual proxy and Final. The independent international portal `w.mgtv.com`, download hosts, images, media CDN and unverified native-client endpoints stay on their original routes. Both mainland and overseas storefronts point to the same included host, which also holds international terms, so all requests to that host follow the group, irrespective of path. Mixed egress is possible. No native-client, sign-in, playback, download, copyright or regional eligibility is promised.
