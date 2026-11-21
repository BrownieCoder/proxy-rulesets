# 搜狗输入法手机版公开入口分流依据

基线：`70ae1f46dc8f9bb5a8a3a2709c9db8fe23333631`。新增 `DOMAIN,shouji.sogou.com`，使用独立的 `⌨️ 搜狗输入法手机版` 策略组：默认直连（DIRECT），也可选择节点或 Final。

## 官方依据

- [搜狗手机输入法官网](https://shouji.sogou.com/index.php)：展示移动端下载和帮助；列出的安装包及部分素材在不同主机。
- [搜狗官方使用说明](https://shouji.sogou.com/wap/htmls/instructions.php)：将该精确主机标为手机版产品官网。

证据级别：第一方网页或开发者公开资料，足以说明主机归属和手机产品官网、下载介绍与帮助入口，不等于实测原生客户端。核对使用公开页面，不登录、下载 App 或采集流量。

## 作用与边界

同主机所有路径随组；不另纳入桌面版、独立账号、素材子域或跨主机安装文件；未验证原生输入、云候选与同步链路。 此规则按主机匹配，不按 URL 路径或发起进程匹配。其他主机可走不同出口。

在基线的离线有序域名模型中，此主机原先首先命中 `ChinaMax → 🇨🇳 China-Global`。新增是提供独立选项，不代表此前没有通用覆盖。顺序位于现有 App 之后、SiriAI 和通用规则之前；保留安全与游戏优先及末尾 MATCH。离线结果不代表 DNS、GeoIP、UDP 或真实 App 行为。

保持原策略的对照：`sogou.com`、`pinyin.sogou.com`、`shurufa.sogou.com`、`account.sogou.com`、`indivi-cdn.shouji.sogou.com`、`img.shouji.sogou.com`、`apkdl.sogouimecdn.com`、`pb.i.sogou.com`，另含子域、相似标签和规避误匹配的后缀对照。

## English scope

Only `shouji.sogou.com` gets a dedicated DIRECT-first selector for Sogou Mobile IME. This covers all paths on that host, not all traffic from the app. Other hosts keep their existing routes; native-client and real-network behavior were not tested.
