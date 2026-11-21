# 微信读书公开入口分流依据

基线：`bb222d1e8c634fbd95c9017acd10846421d1252c`。仅收录 `weread.qq.com`（1 条精确 DOMAIN），新增独立 `📚 微信读书`：默认直连，可手动选择节点或 Final。

## 官方证据

- [中国 App Store 微信读书](https://apps.apple.com/cn/app/id952059546)：腾讯开发者介绍明确声明 weread.qq.com 为官方网站。
- [微信读书官方网页](https://weread.qq.com/)：本次匿名网页读取显示书籍目录和登录入口，未点登录或下载。
- [官方隐私说明](https://weread.qq.com/policy)：同主机有产品隐私说明，佐证归属而非全链路。

证据只说明主机归属与公开用途。在公开网页和开发者资料上核实，不登录、不获取安装包、账号数据或私人配置。

## 范围与路由

同主机全部路径随组，可能含同主机登录及阅读内容。另域微信聊天、公众号、QQ 阅读、认证与素材 CDN 保持原路由，不保证客户端阅读、支付或会员。 精确 DOMAIN 只限制主机，不限制路径，同主机的其他用途也随组。别名、其他域名及未核实的服务仍走原策略，切换时可能出现混合出口；未实测完整客户端网络、DNS、IP/GeoIP 或 UDP。

在基线公开模板与规则集的离线域名模拟中，上述主机原本由 `ChinaMax → 🇨🇳 China-Global` 首匹配；新增只是提供独立出口，不是首次覆盖，也不代表此前路由故障。引用放在得物和既有 App 之后、SiriAI 与宽泛集合之前；安全与游戏仍优先，最后的 MATCH 不变。

排除并验证对照：`weixin.qq.com`、`mp.weixin.qq.com`、`im.qq.com`、`y.qq.com`、`yuedu.qq.com`、`myqcloud.com`。匹配模型仅覆盖有域名、没有 IP 和进程元数据的离线探针。参见 [Mihomo 固定版本域名构造源码](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)。

## English scope

Only `weread.qq.com` receive an independent DIRECT-first policy for WeRead. All paths on each listed host use the same selector, but other hosts keep prior routing. This is not a claim of complete native-client routing, authentication, payment, or real-network validation.
