# 得物公开官网入口分流依据

核实日期：2026-11-21。公开基线：`9b0a5eb64c9a241b1bcd049c8526af7c97768571`。

## 来源与接受范围

| 精确主机 | 官方证据和观察 | 纳入理由、置信度与边界 |
| --- | --- | --- |
| `dewu.com` | [裸根官网](https://dewu.com/) 的网页读取在同一主机显示得物 App 官方介绍、下载入口和运营者上海得物信息集团有限公司 | 高置信官方公开入口，使用 `DOMAIN`。本次网页读取未报告跨主机跳转，不保证所有地区或时点一致。 |
| `www.dewu.com` | [带 www 的官网](https://www.dewu.com/) 同样展示官方 App 下载入口及运营者；[国内 App Store](https://apps.apple.com/cn/app/id1012871328) 列出的开发者为同一公司 | 高置信独立可访问的官方公开入口，使用 `DOMAIN`。App Store 开发者身份不是 Apple 对网站、整条下载链路或客户端域名归属的验证。 |

只匿名读取介绍与公开渠道。网页观察不是现场 DNS 或 HTTP 状态测量；不登录、不获取安装包，不下单、不访问个人鉴别结果或支付流程。

## 未收录范围

- `cdn.dewu.com` 是官网公开图片引用的素材主机。App Store 的开发者隐私链接指向 `cdn-fast.dewu.com`，目标页在本环境读取超时。官网素材或单个隐私政策链接不足以证明这些 CDN 的全主机用途。
- 官网单独链接国际卖家 `www.poizon.com`、商家后台 `stark.dewu.com`、开放平台 `open.dewu.com`，以及创作者和机构平台 `creator.dewu.com`、`livemcn.dewu.com`、`liveplatform.dewu.com`、`mcn.dewu.com`，均不纳入。协议子域 `agreement.dewu.com` 和独立 `dewucdn.com` 域也沿原路由。
- 目标主机上的社区、个人卖家、条款以及其他所有路径会随 `👟 得物` 策略，主机规则无法按路径或功能隔离。其他主机继续原策略，手动改选代理可能形成混合出口。
- 不使用裸根后缀或通配符，不推断 App API、认证、鉴别、订单、支付或文件主机。不保证原生 App、下载、登录、鉴别、交易、支付、地区资格或网络性能。

## 基线和验收

使用仓库公开规则、provider manifest 和现有无 IP/进程元数据的 matcher 离线模拟：两个目标和上述排除主机都先命中 `ChinaMax → 🇨🇳 China-Global`。新组只是把这两个入口单独交给用户选路，默认 DIRECT，保留手动代理和 Final；不声称已有规则失效，也不知道用户本地策略当前选了哪个出口。

只在微博之后、SiriAI 之前插入一个专属引用，保留所有旧规则的相对次序。校验固定两个 exact 主机、唯一引用、策略组选项、首匹配及负控不变；正确的 Privacy/REJECT 和 Hijacking 拦截仍可优先。离线检查按 [Mihomo 的域名规则构造方式](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L33) 比对 ASCII 域名大小写；不模拟国际化域名或 IP 条件。真实客户端、DNS、IP/GeoIP 和 UDP 未实测。生成资产由现有离线生成器维护；不改镜像、来源或权限。

## English scope

Only the exact public portals `dewu.com` and `www.dewu.com` receive a selectable DIRECT-first policy. The operator's pages and mainland App Store developer listing support their public identity. Every path on those hosts follows the policy, including community, seller, and agreement pages; separate CDN, merchant, platform, and international POIZON hosts retain their routes. Mixed egress is possible. This does not validate or cover the native app, downloads, sign-in, authentication of goods, transactions, payments, or regional eligibility.
