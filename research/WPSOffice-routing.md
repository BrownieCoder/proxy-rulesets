# WPS Office 精确公开入口分流依据

核实日期：2026-11-18。基线 `74b4640cfb0d8cef4395fb199f8e9f8903fcd84e`。

## 来源、范围与证据边界

仅查看匿名官方公开页面和入口链接，不登录，不提交文档，不请求下载包、认证、支付或私有接口。来源事实与离线路由模拟分开记录；不保存原始网页、响应头、查询参数或账户数据。

| 精确主机 | 官方来源与本轮核实 | 用途、目标、置信度及影响 |
| --- | --- | --- |
| `www.wps.cn` | [WPS 官方首页](https://www.wps.cn/)当前展示 WPS Office，并在该产品导航列出 Windows、Mac、Linux 入口 | 官方公开门户，默认 `DIRECT`，可选代理与 Final。高：页面内容与入口已核实；主机规则影响全部路径，包括同主机上的 WPS 365 / AI 营销内容，不能按产品或路径隔离 |
| `platform.wps.cn` | 上述官网 WPS Office 导航的实际 Windows 链接指向[此主机](https://platform.wps.cn/) | 官方声明的 Windows 产品入口，默认 `DIRECT`，可选代理与 Final。高：官方链接声明；本轮目标页面抓取超时，未验证其页面内容、重定向或下载链路。规则影响同主机全部路径 |
| `mac.wps.cn` | 上述官网 WPS Office 导航的实际 Mac 链接指向[此主机](https://mac.wps.cn/) | 官方声明的 Mac 产品入口，默认 `DIRECT`，可选代理与 Final。高：官方链接声明；本轮目标页面抓取超时，未验证其页面内容、重定向或下载链路。规则影响同主机全部路径 |
| `linux.wps.cn` | 官网的实际 Linux 链接指向[WPS Office for Linux 官方页](https://linux.wps.cn/)，本轮页面可读且标题明确；页面列出 Linux 安装格式，未点击下载 | Linux 公开产品说明入口，默认 `DIRECT`，可选代理与 Final。高：官方链接与产品页面；不代表安装包最终主机、完整下载或客户端已实测。规则影响同主机全部路径 |

四个主机在基线的真实有序域名模型中均为 `ChinaMax → 🇨🇳 China-Global`。增加独立策略的价值是明确出口控制，不是首次覆盖，也不意味着原先连接有故障。

## 明确排除与使用限制

- 不添加 `wps.cn`、`wpscdn.cn`、`kdocs.cn` 等共享根域后缀，不添加任何 CDN、猜测的 API、认证、云存储、上传、同步或支付主机。
- 官网还链接 WPS 365、WPS AI / Comate、稻壳模板、金山文档、企业版、客服与开放平台。本批不把这些不同产品或共享业务的独立主机合入 WPS Office：例如 `365.wps.cn`、`comate.wps.cn`、`docer.wps.cn`、`www.kdocs.cn`、`ep.wps.cn`、`mo.wps.cn`、`helpdesk.wps.cn`、`open.wps.cn`。
- 只有四个精确主机跟随独立组；其他主机仍按原规则，手动代理可能产生混合出口。主机级规则作用于全部路径，不能承诺仅影响下载介绍页，也不能在同主机内排除营销、业务或遥测路径。已有合法 Privacy / Hijacking 拦截优先。
- 不是完整原生 App、编辑、同步、云文档上传、AI 或下载链路控制；不保证功能、速度、地区、付费权限或 AI 资格。未实测真实客户端、DNS、GeoIP、文件传输、账户或网络可用性。

## 最小实施计划（待独立审查）

目标是为已核实入口提供独立且默认直连的可选策略，不扩大其他 WPS 产品范围。约束为公开材料、来源许可、安全/游戏优先、所有 21 个既有 App 相对顺序、既有 FINAL，以及权限和共享验证器零变化。

1. `APPROVE FOR IMPLEMENTATION` 候选：新增 `ruleset/WPSOffice.yaml` 四条精确 `DOMAIN`、`WPSOffice` 本地登记、`📝 WPS Office` 的 DIRECT-first select 组（保留已有手动代理与 Final）、`办公` 目录项。独立规则放在全部既有 App（含 Youku）之后、SiriAI 之前；只增加一个引用，不重排旧规则。
2. `APPROVE FOR IMPLEMENTATION` 候选：只新增自身 `validate_wps_office(root)` 与一个 tree 调用，复用现有 `app_policy` / 结构读取合同。固定四主机、唯一引用、策略选项、先后顺序、真实 first-match 与非目标负控；未知或不完整规则、空白字段、缺失/冲突 provider、前置 IP 条件均失败关闭。旧函数、共享模块、镜像、来源锁及工作流不改。
3. 验收：完整公开 fixture 正向，helper 与真实 tree 的范围、顺序、策略组复杂 YAML、结构错误、合法安全更新、非安全抢先、未知 provider/IP、空白字段、UTF-8 等实际变异回归；失败来自目标合同而不是缺文件。全树可由更早的同原因门禁拒绝，不强锁 WPS 专属前缀。
4. 通过现有离线生成器维护派生页、目录、provider 与 hash；执行针对测试、默认验证、公开检查、生成一致性、diff 检查，完整测试由整批统一调度。精确本地候选再交独立复核；独立 commit / PR，不与其他 App 混合，不合并。

## English scope summary

Add only four exact public WPS Office entry hosts: `www.wps.cn`, `platform.wps.cn`, `mac.wps.cn`, and `linux.wps.cn`. The official homepage explicitly links the latter three as Windows, Mac, and Linux product entries; the Linux page was also readable. Windows and Mac destination fetches timed out in this check, so their evidence is the official link declaration, not verified destination content or download behavior. No download, sign-in, document, API, payment, or account operation was performed. All paths on each included host follow the optional DIRECT-first group; the shared homepage also markets other products. Separate WPS 365, AI, enterprise, template, cloud-document, and CDN hosts remain out of scope. This is partial entry routing with possible mixed egress, not a native-editing, sync, upload, download, AI-feature, eligibility, or connectivity guarantee. Existing security/game/App precedence and permissions remain unchanged.
