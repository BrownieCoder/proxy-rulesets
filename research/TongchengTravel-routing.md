# 同程旅行公开入口分流依据

基线：`f97659bda37554392e2d4a5407bbc644ac2b7a39`。新增 `DOMAIN,m.ly.com`，使用独立的 `🧳 同程旅行` 策略组：默认直连（DIRECT），也可以选择节点或 Final。

## 官方依据

- [同程移动官网](https://m.ly.com/public/index)：公开旅行入口提供客户端链接，点击目标是另一个主机，本规则不纳入。
- [同程官方帮助](https://www.ly.com/newhelp/questionlist/1-1-469.html)：分别列出移动网页和 App 渠道；这不是将网页流量等同于原生客户端流量。

证据级别：第一方网页或开发者公开声明，足以确认主机归属和移动旅行网页及 App 导流入口，不作为已实测原生 App 网络的证据。核对只使用公开页面，没有登录、触发交易或采集客户端流量。

## 作用与边界

同主机的全部路径使用同一策略（可能包括移动网页预订流程）。下载链接指向另域 m.17u.cn，不会随组；桌面站、企业商旅、独立登录、票务或支付不视为已验证。 精确规则匹配的是主机而不是 URL 路径，也不会只匹配某一个 App 或进程。同一主机从其他客户端打开同样随组；其他主机可能使用不同出口。

在基线有序模板的离线域名模拟中，该主机原先首次匹配 `ChinaMax → 🇨🇳 China-Global`。新增仅将已知入口单独分组，不代表此前不覆盖。引用放在已有 App 之后、SiriAI 与宽泛规则之前；保留安全、游戏优先及末尾 MATCH。

排除并验证的对照：`ly.com`、`www.ly.com`、`m.17u.cn`、`tmc.ly.com`、`passport.ly.com`、`pic5.40017.cn`、`www.12306.cn`、`m.ctrip.com`，另含同主机的子域、相似标签与不同后缀。参见 [Mihomo 固定版本的域名匹配源码](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)。模型仅验证无 IP 或进程信息的域名，不代表 DNS、GeoIP、UDP 或真实客户端结果。

## English scope

Only `m.ly.com` gets a dedicated DIRECT-first selector for Tongcheng Travel. This matches all paths on that host; other hosts are unchanged and may use different egress. It does not cover the complete native app or assert real-network, sign-in, or transaction behavior.
