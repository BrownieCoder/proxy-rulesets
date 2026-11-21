# 盒马公开入口分流依据

基线：`bb222d1e8c634fbd95c9017acd10846421d1252c`。仅收录 `www.freshhema.com`、`www.freshippo.com`（2 条精确 DOMAIN），新增独立 `🛒 盒马`：默认直连，可手动选择节点或 Final。

## 官方证据

- [中国 App Store 盒马](https://apps.apple.com/cn/app/id1063183999)：开发者网站明确链接 www.freshhema.com，本次点链接返回 www.freshippo.com。
- [盒马公开官网](https://www.freshippo.com/)：本次读取确认官方页标题，页面需脚本才有完整内容，不宣称购买或下载已实测。

证据只说明主机归属与公开用途。在公开网页和开发者资料上核实，不登录、不获取安装包、账号数据或私人配置。

## 范围与路由

两个官网入口的所有路径同组。另域淘宝、阿里共享 CDN 和其他子域保持原路由；不保证原生下单、结算或配送链路。 精确 DOMAIN 只限制主机，不限制路径，同主机的其他用途也随组。别名、其他域名及未核实的服务仍走原策略，切换时可能出现混合出口；未实测完整客户端网络、DNS、IP/GeoIP 或 UDP。

在基线公开模板与规则集的离线域名模拟中，上述主机原本由 `ChinaMax → 🇨🇳 China-Global` 首匹配；新增只是提供独立出口，不是首次覆盖，也不代表此前路由故障。引用放在得物和既有 App 之后、SiriAI 与宽泛集合之前；安全与游戏仍优先，最后的 MATCH 不变。

排除并验证对照：`freshhema.com`、`freshippo.com`、`terms.alicdn.com`、`www.taobao.com`、`www.tmall.com`。匹配模型仅覆盖有域名、没有 IP 和进程元数据的离线探针。参见 [Mihomo 固定版本域名构造源码](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)。

## English scope

Only `www.freshhema.com`, `www.freshippo.com` receive an independent DIRECT-first policy for Freshippo. All paths on each listed host use the same selector, but other hosts keep prior routing. This is not a claim of complete native-client routing, authentication, payment, or real-network validation.
