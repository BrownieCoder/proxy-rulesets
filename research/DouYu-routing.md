# 斗鱼公开入口分流依据

基线：`f97659bda37554392e2d4a5407bbc644ac2b7a39`。新增 `DOMAIN,m.douyu.com`，使用独立的 `🐟 斗鱼` 策略组：默认直连（DIRECT），也可以选择节点或 Final。

## 官方依据

- [斗鱼移动官网](https://m.douyu.com/)：公开移动直播目录显示打开 App 入口。
- [斗鱼官方赛事公告](https://www.douyu.com/cms/detail/new_list/11607.shtml)：分别标示独立的桌面直播间和该主机下的移动端入口。

证据级别：第一方网页或开发者公开声明，足以确认主机归属和移动直播网页及打开 App 入口，不作为已实测原生 App 网络的证据。核对只使用公开页面，没有登录、触发交易或采集客户端流量。

## 作用与边界

同主机的全部路径（包括直播间页面）使用同一策略；桌面站、视频站、游戏、独立 CDN 和认证主机不纳入，不承诺原生直播流或弹幕走同一出口。 精确规则匹配的是主机而不是 URL 路径，也不会只匹配某一个 App 或进程。同一主机从其他客户端打开同样随组；其他主机可能使用不同出口。

在基线有序模板的离线域名模拟中，该主机原先首次匹配 `ChinaMax → 🇨🇳 China-Global`。新增仅将已知入口单独分组，不代表此前不覆盖。引用放在已有 App 之后、SiriAI 与宽泛规则之前；保留安全、游戏优先及末尾 MATCH。

排除并验证的对照：`douyu.com`、`www.douyu.com`、`v.douyu.com`、`wan.douyu.com`、`staticlive.douyucdn.cn`，另含同主机的子域、相似标签与不同后缀。参见 [Mihomo 固定版本的域名匹配源码](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)。模型仅验证无 IP 或进程信息的域名，不代表 DNS、GeoIP、UDP 或真实客户端结果。

## English scope

Only `m.douyu.com` gets a dedicated DIRECT-first selector for DouYu. This matches all paths on that host; other hosts are unchanged and may use different egress. It does not cover the complete native app or assert real-network, sign-in, or transaction behavior.
