# 腾讯 QQ 公开入口分流依据

核实日期：2026-11-21。基线：`9b0a5eb64c9a241b1bcd049c8526af7c97768571`。仅收录 `DOMAIN,im.qq.com`，使用独立选择组 `🐧 腾讯 QQ`：优先 DIRECT，保留手动节点和 Final。

## 官方证据与边界

| 精确主机 | 官方来源 | 用途与证据强度 |
| --- | --- | --- |
| `im.qq.com` | [中国 Mac App Store 的 QQ](https://apps.apple.com/cn/app/qq/id451108668?mt=12)「开发者网站」链接指向此主机，腾讯开发者介绍也明确给出同主机的 Mac QQ 产品页；[腾讯 QQ Windows 公开页](https://im.qq.com/pcqq/)网页读取返回同主机 `/pcqq/index.shtml`，显示 Windows 端简介及下载按钮 | 高置信官方公开入口和客户端介绍。网页读取不等于验证 HTTP 状态、所有地区行为、下载文件或 App 后台连接；未点击下载，不登录 |

[中国 iOS App Store 的 QQ](https://apps.apple.com/cn/app/qq/id444934666)用于确认产品和开发者身份，并不作为该页面声明官网的依据。腾讯 [产品目录](https://www.tencent.net.cn/zh-cn/what-we-create/everything-we-create/)分别列出 QQ、QQ 空间、腾讯视频、腾讯游戏、QQ 邮箱等，不把它们当作同一分流对象。

- 单个 exact 主机的全部路径同组，包括不同客户端和其他入口导航；不是只分流某个下载页面，也不意味着页面或客户端访问的其他主机随之切换。
- 不收录 `qq.com` 后缀、`gtimg.com`、`gtimg.cn` 或任何共享腾讯 CDN、安装包、登录、本地账号及未验证的聊天/API 主机。QQ 邮箱、QQ 空间、QQ 音乐、微信、腾讯视频、腾讯游戏有各自边界。
- 只读取公开网页或开发者元数据，不登录、不获取安装文件，不保存用户资料、认证请求或私人配置。其他请求保留原路，手动代理可能造成混合出口；异常时可切回 DIRECT 排查。未实测聊天、音视频、登录、文件传输、下载或地区识别。

## 路由与验证

当前有序规则和公开 provider 的离线域名模拟中，`im.qq.com` 首先由 `ChinaMax → 🇨🇳 China-Global` 命中；新增专属出口不是在修复原路由故障。不从公共策略名推断用户实际出口。规则放在微博及既有 App 后、SiriAI 与宽泛 provider 前；安全与游戏保持优先。

负控包括 `y.qq.com`（QQ 音乐）、`v.qq.com`（腾讯视频）、`weixin.qq.com`（微信）、`game.qq.com`（国内游戏）、`mail.qq.com`、`qzone.qq.com`、`dldir1.qq.com`、`child.im.qq.com` 和 `im.qq.com.example.org`。对照基线而不假定所有负控都落到 MATCH。测试覆盖同名规则、范围变宽、选项与结构、配置引用、前置域名及合法安全命中；[Mihomo 固定版本的 DOMAIN 构造器](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)会将域名参数转为小写，前置大写 ASCII 或含 Unicode 带点大写 I 的同形域名也要检测。这不是通用 IDN 归一化，模型不替代 DNS、GeoIP、UDP 或真实网络测试。

## English scope summary

Only the exact public entry host `im.qq.com` gains a DIRECT-first policy, supported by Tencent’s Mac App Store developer website link and official Windows information page. All paths on that host share the same policy. Other QQ/Tencent hosts, authentication, delivery infrastructure, and unrelated products keep their existing routing. This does not claim end-to-end native app, login, chat, media, or installer coverage.
