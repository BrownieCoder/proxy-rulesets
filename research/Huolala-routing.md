# 货拉拉公开入口分流依据

基线：`bb222d1e8c634fbd95c9017acd10846421d1252c`。仅收录 `www.huolala.cn`（1 条精确 DOMAIN），新增独立 `🚚 货拉拉`：默认直连，可手动选择节点或 Final。

## 官方证据

- [货拉拉公司官网](https://www.huolala.cn/)：首页展示正式货拉拉产品，并提供用户端下载入口；未获取安装文件。
- [中国 App Store 货拉拉](https://apps.apple.com/cn/app/id940562664)：国内客户端开发者说明声明官方网站。

证据只说明主机归属与公开用途。在公开网页和开发者资料上核实，不登录、不获取安装包、账号数据或私人配置。

## 范围与路由

只纳入这个官网主机；另域开放平台、下载、平行物流站和国际 Lalamove 保持原路由，不保证下单、司机端、支付或定位。 精确 DOMAIN 只限制主机，不限制路径，同主机的其他用途也随组。别名、其他域名及未核实的服务仍走原策略，切换时可能出现混合出口；未实测完整客户端网络、DNS、IP/GeoIP 或 UDP。

在基线公开模板与规则集的离线域名模拟中，上述主机原本由 `ChinaMax → 🇨🇳 China-Global` 首匹配；新增只是提供独立出口，不是首次覆盖，也不代表此前路由故障。引用放在得物和既有 App 之后、SiriAI 与宽泛集合之前；安全与游戏仍优先，最后的 MATCH 不变。

排除并验证对照：`huolala.cn`、`wuliu.huolala.cn`、`open.huolala.cn`、`dappweb.huolala.cn`、`huolala.co`、`www.hllep.com`、`www.lalamove.com`。匹配模型仅覆盖有域名、没有 IP 和进程元数据的离线探针。参见 [Mihomo 固定版本域名构造源码](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)。

## English scope

Only `www.huolala.cn` receive an independent DIRECT-first policy for Huolala. All paths on each listed host use the same selector, but other hosts keep prior routing. This is not a claim of complete native-client routing, authentication, payment, or real-network validation.
