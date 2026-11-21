# 腾讯文档公开入口分流依据

基线：`f97659bda37554392e2d4a5407bbc644ac2b7a39`。新增 `DOMAIN,docs.qq.com`，使用独立的 `📝 腾讯文档` 策略组：默认直连（DIRECT），也可以选择节点或 Final。

## 官方依据

- [腾讯文档官网](https://docs.qq.com/index.html)：同主机进入在线文档官网；不访问私有文档、不登录。
- [中国 App Store](https://apps.apple.com/cn/app/%E8%85%BE%E8%AE%AF%E6%96%87%E6%A1%A3/id1370780836)：腾讯开发者资料将 docs.qq.com 标示为官方网站。

证据级别：第一方网页或开发者公开声明，足以确认主机归属和官网及同主机在线文档网页，不作为已实测原生 App 网络的证据。核对只使用公开页面，没有登录、触发交易或采集客户端流量。

## 作用与边界

同主机所有路径（包括网页文档与编辑器）使用同一策略；不扩展到 QQ、微信、腾讯会议、认证、共享资源或原生同步主机。 精确规则匹配的是主机而不是 URL 路径，也不会只匹配某一个 App 或进程。同一主机从其他客户端打开同样随组；其他主机可能使用不同出口。

在基线有序模板的离线域名模拟中，该主机原先首次匹配 `ChinaMax → 🇨🇳 China-Global`。新增仅将已知入口单独分组，不代表此前不覆盖。引用放在已有 App 之后、SiriAI 与宽泛规则之前；保留安全、游戏优先及末尾 MATCH。

排除并验证的对照：`qq.com`、`im.qq.com`、`meeting.tencent.com`、`work.weixin.qq.com`、`beacon.qq.com`、`weread.qq.com`、`gtimg.com`，另含同主机的子域、相似标签与不同后缀。参见 [Mihomo 固定版本的域名匹配源码](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)。模型仅验证无 IP 或进程信息的域名，不代表 DNS、GeoIP、UDP 或真实客户端结果。

## English scope

Only `docs.qq.com` gets a dedicated DIRECT-first selector for Tencent Docs. This matches all paths on that host; other hosts are unchanged and may use different egress. It does not cover the complete native app or assert real-network, sign-in, or transaction behavior.
