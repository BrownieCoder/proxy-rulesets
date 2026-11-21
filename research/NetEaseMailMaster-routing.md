# 网易邮箱大师公开入口分流依据

基线：`bb222d1e8c634fbd95c9017acd10846421d1252c`。仅收录 `dashi.163.com`（1 条精确 DOMAIN），新增独立 `📧 网易邮箱大师`：默认直连，可手动选择节点或 Final。

## 官方证据

- [网易邮箱官方帮助：下载入口](https://help.mail.126.com/faqDetail.do?code=d7a5dc8471cd0c0e8b4b8f4f8e49998b374173cfe9171305fa1ce630d7f67ac2cc74999dfd3e96a6)：官方帮助明确指向 dashi.163.com；独立匿名 GET 返回 200，但未确认完整页面或下载行为。
- [网易邮箱官方帮助：网页版](https://help.mail.126.com/faqDetail.do?code=d7a5dc8471cd0c0e8b4b8f4f8e49998b374173cfe9171305fa1ce630d7f67ac2563520832b0ba1e3)：明确同一主机还含产品网页版登录；不进行登录或收发邮件测试。

证据只说明主机归属与公开用途。在公开网页和开发者资料上核实，不登录、不获取安装包、账号数据或私人配置。

## 范围与路由

同主机网页登录路径也随组；不接 163/126 通用邮箱、企业邮、独立认证、邮件协议或共享网易资源。 精确 DOMAIN 只限制主机，不限制路径，同主机的其他用途也随组。别名、其他域名及未核实的服务仍走原策略，切换时可能出现混合出口；未实测完整客户端网络、DNS、IP/GeoIP 或 UDP。

在基线公开模板与规则集的离线域名模拟中，上述主机原本由 `ChinaMax → 🇨🇳 China-Global` 首匹配；新增只是提供独立出口，不是首次覆盖，也不代表此前路由故障。引用放在得物和既有 App 之后、SiriAI 与宽泛集合之前；安全与游戏仍优先，最后的 MATCH 不变。

排除并验证对照：`mail.163.com`、`mail.126.com`、`mail.qq.com`、`maas.mail.163.com`、`reg.163.com`、`smtp.163.com`、`imap.163.com`、`pop.163.com`。匹配模型仅覆盖有域名、没有 IP 和进程元数据的离线探针。参见 [Mihomo 固定版本域名构造源码](https://github.com/MetaCubeX/mihomo/blob/0455d0d28c4526937380505153e65a843d8612e8/rules/common/domain.go#L29-L35)。

## English scope

Only `dashi.163.com` receive an independent DIRECT-first policy for NetEase Mail Master. All paths on each listed host use the same selector, but other hosts keep prior routing. This is not a claim of complete native-client routing, authentication, payment, or real-network validation.
