# 微信公开官网精确分流依据

核实日期：2026-11-19。基线：`70c33529edef85b38eb845a7edf96cccea06067c`。已接受范围仅一个精确主机 `weixin.qq.com`；这不是完整微信客户端分流。

## 官方证据与范围

仅匿名读取公开页面，不登录、不带 Cookie、不请求安装包或页面声明的资源，不抓取私人流量。以下是官网归属与公开入口证据，不是聊天、支付或客户端服务链路测试。

| 精确主机 | 主源与本轮观察 | 用途、置信度与影响 |
| --- | --- | --- |
| `weixin.qq.com` | [微信官网](https://weixin.qq.com/)匿名 HTTPS GET 返回 200，最终主机仍为 `weixin.qq.com`，标题“微信，是一个生活方式”；[腾讯微信产品页](https://www.tencent.com/zh-cn/products/weixin-wechat/)返回 200，标题“微信 & WeChat - Tencent”，实际 `a[href]` 指向该主机；[国内 App Store 微信页面](https://apps.apple.com/cn/app/id414478124)的开发者网站和隐私政策链接均使用该主机 | 高置信官方公开入口。默认 DIRECT，可选现有代理与 Final；主机全部路径随策略，包括条款、宣传及任何现有或未来同主机的业务、统计路径，不能按产品或路径隔离。App Store 链接是开发者声明，不等于 Apple 独立验证 |

网页提取器最初无法打开官网；后续受控普通匿名 HTTPS 请求成功，以上响应与标题来自该请求。此次没有跨主机跳转，不保证其他时间、地区或路径不发生跳转；重定向后的其他主机仍走原策略。

## 排除项与边界

- 仅接受 `DOMAIN,weixin.qq.com`，不添加 `DOMAIN-SUFFIX,weixin.qq.com`、整个 `qq.com`、`wx.qq.com`、`wechat.com` 或任何腾讯共享命名空间。
- 官网实际 `a[href]` 还声明以下不同主机：`ad.weixin.qq.com`、`car.weixin.qq.com`、`channels.weixin.qq.com`、`cover.weixin.qq.com`、`developers.weixin.qq.com`、`filehelper.weixin.qq.com`、`fuwu.weixin.qq.com`、`game.weixin.qq.com`、`iot.weixin.qq.com`、`kids.weixin.qq.com`、`linux.weixin.qq.com`、`mac.weixin.qq.com`、`mp.weixin.qq.com`、`open.weixin.qq.com`、`openai.weixin.qq.com`、`pay.weixin.qq.com`、`pc.weixin.qq.com`、`search.weixin.qq.com`、`sticker.weixin.qq.com`、`store.weixin.qq.com`、`work.weixin.qq.com`、`z.weixin.qq.com`、`kf.qq.com`、`weixin110.qq.com`、`www.wechat.com`、`wechat.design`、`www.tencent.com`，均不纳入本批；没有请求这些目的页。这不否认其品牌关联。
- 官网实际 `script` / `link` / `img` 声明的资源主机 `res.wx.qq.com`、`res.wxqcloud.qq.com.cn` 排除；仅核实 HTML 引用，没有获取资源，不据此接管整台共享主机。
- 不猜聊天、通知、登录、鉴权、文件传输、通话、支付、小程序或视频号接口。未观察到的接口外形不作为正式来源或正式规则。
- 排除其他游戏、广告或业务主机不等于按路径排除：列出主机的全部路径都生效；其他主机仍走原策略，切代理可能形成 mixed egress。遇会话或地区异常可以恢复 DIRECT 排查，未实测风控或修复效果。
- 不保证原生微信、聊天、通话、朋友圈、公众号、小程序、支付、登录、下载或安装包完整链路，不改变账号、会员、速度或地区资格。没有实测 DNS、GeoIP、UDP、IP / 进程元数据、代理连通性或真实客户端。

## 当前首匹配与最小接入合约

读取基线的两个公共 manifests、53 个 provider 和 66 条实际有序规则，既有 `DomainRules` 域名模型中 `weixin.qq.com` 只命中 ChinaMax 的 `DOMAIN-SUFFIX,qq.com`，首匹配为 `ChinaMax → 🇨🇳 China-Global`；安全、游戏和 25 个既有 App 不抢占。不存在微信专属 provider。价值是官网入口可以独立选择出口，不是首次覆盖，也不说明旧路由有故障，不能推断私人配置当前选择的出口。

1. Provider `WeChat`、目录 id `wechat`、分类“社交”，独立 `💬 微信` literal select，DIRECT-first，保留 `🚀 节点选择` 和 `🧭 Final`。只增加一个活动引用，位于全部 25 个旧 App（含 WPS Office、飞书、钉钉和夸克）之后、SiriAI 之前；旧规则相对顺序、安全与游戏、Gemini / Google、MATCH 均保持。
2. 仅新增本 App 的真实验证入口与一次 tree hook；复用既有 `app_policy`、`public_rules`、`public_policy_groups` 受限且 fail-closed 的公共模板语法，不重写共享模块或旧 App。覆盖固定范围、唯一引用与标记、前后顺序、DIRECT / 代理 / Final、复杂 YAML、manifest 冲突 / 缺失、未知 / 不完整 / 空白规则字段、前置 IP 条件与 UTF-8。
3. 完整公共临时 fixture 先真实通过，再进行 scope、结构、策略、顺序和首匹配变异。合法 Privacy/REJECT、Hijacking/劫持组更新仍可优先；非安全抢占和错误目标必须失败。直接 helper 保持自身准确诊断，完整树允许更早门禁按具体原因拒绝。策略结构测试的显式 App 清单追加微信。
4. 独立固定负控包括全部上述排除主机、裸根 / 相似域名与目标子域、QQ 音乐、腾讯视频、安全追踪主机、旧 App、Siri、国际游戏、Claude 和 `example.org`。启用 / 关闭本组时非目标首匹配必须不变；例如 `y.qq.com` 保持 QQMusic、`v.qq.com` 保持 TencentVideo、`beacon.qq.com` 保持 Privacy/REJECT。
5. 使用现有离线生成器更新派生目录与 providers；验证专项、默认检查、生成一致性和固定候选的完整测试。研究和实现独立提交；不运行网络同步，不修改镜像、来源锁、依赖、工作流、权限或私有配置。

## English scope summary

Accepted scope: the single exact official public entry `weixin.qq.com`. An anonymous homepage GET returned HTTP 200 on the same host; Tencent's product page and the developer's Chinese App Store website/privacy links independently declare it. This establishes public entry attribution, not native-client network coverage or service availability. The initial page extractor failed, so the successful ordinary HTTPS observation is recorded separately.

All paths on this host follow an optional DIRECT-first group with manual proxy and Final options. Other Weixin subdomains, international WeChat hosts and shared resources remain excluded; this is not a path-level exclusion. Cross-host redirects and resources keep their original routes and may create mixed egress. No chat, calls, payments, authentication, Mini Program, file transfer, download, native-app, account or regional guarantee is made. Security, gaming, all 25 existing App routes and unchanged shared validators, permissions and provenance remain protected.
