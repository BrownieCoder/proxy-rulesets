# 快手公开入口精确分流研究

## 当前决定与范围

经方案审查，已接受首批范围仅为 `www.kuaishou.com`、`m.kuaishou.com` 两个精确 `DOMAIN`，提供 `📹 快手` 独立策略，默认 `DIRECT`，保留手动代理。资源主机虽有官方引用，但没有足够的主机专属范围证据，不为凑齐资源链扩大清单；实现只提供部分公开入口控制，不表示安装包或播放链路已验证。

基线：`a1c2dd26337b7277019a8764785cdf258bb6f045`。两主机当前离线首匹配均为 `ChinaMax → 🇨🇳 China-Global`，新增价值是独立入口出口控制，不是此前没有覆盖。

## 官方来源与逐主机证据

2026-11-16 只读取匿名官方公开 HTML，提取实际 `a[href]`、`link[href]`、`script[src]`、`img[src]` 等标签的去参数主机/路径。未登录、携带个人 Cookie、抓取私人流量、访问账户接口或下载可执行文件；没有保存完整页面、响应头、请求标识或带参数链接。

| 已接受精确主机 | 官方来源和实际观察 | 用途 / 目标 | 置信度与影响范围 |
| --- | --- | --- | --- |
| `www.kuaishou.com` | [快手品牌官网](https://www.kuaishou.com/cn) 匿名 HTTP 200，页面展示快手 App 品牌；官网有指向本主机 `/` 的实际 `a[href]`。另读取[根入口](https://www.kuaishou.com/)，本次桌面请求跳转至 `/new-reco`，返回 HTTP 200 HTML | 品牌官网和桌面公开入口；默认直连，可选代理 | 高：入口/实际链接证据；影响本主机所有路径，不证明原生 App、视频播放或下载链路 |
| `m.kuaishou.com` | 上述 `/cn` HTML 的实际 `a[href]` 指向 `/download/kwai`，另有 `link[rel=alternate]` 指向本主机。匿名请求[移动入口](https://m.kuaishou.com/)及[官网链接的下载入口](https://m.kuaishou.com/download/kwai)，本次均跳转至 `www.kuaishou.com/new-reco` 的 HTTP 200 HTML | 官网声明的移动/下载访问入口，本次只验证跳转；默认直连，可选代理 | 高：官网关系与跳转证据；不称其返回独立移动业务页，不保证实际安装包下载 |

置信度表示公开页面存在对应入口或引用，不是所有权全面审计、实时可达性、地区资格或原生 App 实测。其他页面读取环境曾对根入口返回 `result: 2` JSON；本记录不把响应差异解释为已证明的服务故障，也没有绕过验证。猜测的 `/download` 路径会进入 404 页面，不作为下载可用性证据。

## 已观察但不纳入的资源

| 主机 | 官方页面实际引用 | 排除理由 |
| --- | --- | --- |
| `s2-11673.kwimgs.com` | `/cn` 中实际 logo、二维码、favicon、CSS 和 script 引用，例如 `/udata/pkg/fe/` 与 `/kos/nlav11673/` 路径 | 页面使用不证明整个主机只属于快手主 App；本轮仅做入口控制，不接管主机全部资源 |
| `static.yximgs.com` | `/cn` 中背景 `img[src]` 和宣传视频 `source[src]`，路径位于 `/udata/pkg/fe/` | 宣传素材不等于原生 App 视频播放链路；共享静态主机不纳入 |
| `p1-plat.wskwai.com` | `/new-reco` 的实际 script、stylesheet、图标引用，路径包括 `/kos/nlav111422/ks-web/` 和 `/udata/pkg/WEB-LIVE/` | 平台资源存在多业务路径线索，没有证明主机专属范围，不能按路径限制域名规则；不把仅 modulepreload 的项当实际请求 |
| `p2-plat.wskwai.com` | `/404` 页面实际 script、stylesheet 和错误页图片引用 | 错误页资源不是完整业务覆盖证据，同样不扩入平台 CDN |

以上只是 HTML 标签声明，不是浏览器网络请求抓包；也未读取或执行这些资源、下载宣传视频或安装包。资源主机保留旧策略，不能宣称本组已覆盖图片、脚本或播放资源。

## 其他明确排除与误伤边界

- 不使用 `kuaishou.com`、`yximgs.com`、`yximg.com`、`kwimgs.com`、`wskwai.com`、`kwai.com` 等根域后缀或通配符，也不按名称猜测 API、音频、视频分片或 CDN 节点。
- 官网实际链接的 `live.kuaishou.com`、`liveopen.kuaishou.com` 属于直播入口/服务，本次不自动扩展到直播和赛事业务；也不加入小游戏、直播伴侣、营销落地页或海外 Kwai。
- `cp.kuaishou.com`、`jigou.kuaishou.com` 等创作者/机构入口、`e.kuaishou.com`、推广/商业平台、支付充值和快手电商不因同属快手自动加入。`www.acfun.cn`、`klingai.kuaishou.com`、一甜相机等关联产品同样排除。
- `wlog.kuaishou.com` 已被公开 Privacy 快照拦截，继续保持 `Privacy → REJECT`；不从网站链接或服务归属推导“应绕过安全拦截”。
- 两条精确规则作用于这两主机的所有路径，不能只限制 `/cn`、推荐页或移动跳转路径；同主机承载的其他页面也会受选择影响。

## 已接受的最小实施范围

目标仅是两个已核实公开入口的独立出口选择。不宣称完整 App、短视频、直播、登录、发布、支付、下载、解锁或账号风控改善。

1. 新增 `ruleset/Kuaishou.yaml` 两条固定 `DOMAIN`，登记本地 provider 和服务目录；说明使用“部分公开入口：默认直连，可选代理”，链接本研究。与其他 App 分开提交、分开 PR。
2. 新增唯一 `📹 快手` `select` 组，`DIRECT` 第一项，保留 `🚀 节点选择` 和 `🧭 Final`。只追加一次 active `RULE-SET,Kuaishou`，位于安全/游戏/现有 App 之后、`SiriAI` 和 Apple/媒体/GeoIP/ChinaMax 等更宽规则之前，不重排原规则。
3. 新增 `validate_kuaishou(root)` 并接入真实 `validate_tree(root)`。严格核对固定两主机、重复/缺失、唯一 active 引用和必要顺序；复用已合并的 `app_policy.validate_select_group`，不另写 type 正则，也不修改共享组件或老 App。保留直连默认、手动代理、唯一组和成员检查；文本读取显式 UTF-8。
4. 以公开规则模型验收真实域名首匹配：允许本组正确目标，或合法 `Privacy → REJECT` / `Hijacking → 🚫 Hijacking` 优先；拒绝非安全抢占、错误 target、未知 provider 和不支持的顶层条件。若本组之前出现顶层 IP/GeoIP 条件，因域名模型无法评估而明确失败，不能当作已证明安全。
5. 临时公开 fixture 中实际调用 helper 和完整 tree，覆盖 scope 扩张、重复/缺失、引用/位置、组默认和代理选项、复杂 type/proxies 键及列表覆盖、未知语法、UTF-8、安全合法更新和非安全抢占；保留独立固定 HOSTS，不能只验证源码形状或规则存在。
6. 负向对照包括各目标的 `child.`、`not` 前缀和 `.example.org` 后缀，所有上述根域/排除资源主机、直播/商业/关联产品、`www.kwai.com`、`wlog.kuaishou.com`、抖音、QQ 音乐和 Siri。比较启用/移除本组时的首匹配，确保非目标仍走原路由。
7. 使用现有离线目录生成器重建 provider 配置、服务页、目录与哈希；执行全 tests、validate、public_check、生成一致性及 diff 检查。复用已验证的 41 services / 288 tests 基线，不改工作流、权限、上游快照、Siri、许可或私人根目录；不运行网络同步。

模型基于公开规则、仅含域名，没有 IP/进程元数据，不能替代真实 DNS、GeoIP、UDP 或 App 验证。手动选代理只改变两主机；图片、脚本、视频、API、直播等其他请求继续沿用旧策略，可能混合出口。如果切换后登录或地区识别异常，可恢复直连排查；这是条件性建议，不是已观测的风控结论。

## English scope summary

Two accepted exact public entry hosts, `www.kuaishou.com` and `m.kuaishou.com`, are evidenced by official anonymous pages and real navigation/alternate links. The mobile/download entry redirected to the desktop recommendation page in this observation; no installer or native-app flow was verified. DIRECT is the default with optional manual proxy control, preserving security and gaming priority. Shared static/CDN hosts, live services, marketing, mini-games, related products and overseas Kwai are excluded. This is not complete app or playback coverage; all paths on each included host are affected, while unlisted requests could use different egress. Validation reuses the existing restricted public-template grammar, not a private-configuration parser or full YAML/network simulation.
