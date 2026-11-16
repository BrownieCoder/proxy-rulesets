# 腾讯视频公开入口精确分流研究

## 状态与建议

`WAITING FOR HUMAN DECISION`：本提交只保存公开来源研究，不改变生产规则、策略组或生成资产。

建议首批只纳入 4 个精确主机：`v.qq.com`、`m.v.qq.com`、`film.qq.com`、`film.video.qq.com`。
它们当前均已有 ChinaMax 覆盖；新增价值是为桌面、移动和公开会员入口提供独立出口选择，不是补齐整个视频播放链路。
拟使用 `📺 腾讯视频` 独立策略，默认 `DIRECT`，保留手动代理选项；范围和策略尚待批准。
腾讯共享根域、共享资源、游戏、其他视频品牌、仅预连接的接口及未知下载目的不纳入。

## 官方公开证据

核实日期：2026-11-16。只读取匿名公开 HTML 和公开重定向头，不登录、不播放、不订购，也未获取安装包、带账号流量或私人配置。
网页提取服务未能读取桌面首页；直接读取官方 HTTPS 页面取得下述内容。仅保留标签、属性、主机与去除查询参数的路径，不保存原始页面、签名查询串或用户内容。
下面的资源引用是 HTML 中的真实声明，不等于已经用浏览器完成资源加载或播放实测。

| 拟纳入精确主机 | Primary source | 实际标签 / 属性 / 路径证据 | 可支持用途与置信度 |
| --- | --- | --- | --- |
| `v.qq.com` | [腾讯视频桌面官网](https://v.qq.com/) | HTTP 200；标题标识腾讯视频；`link[rel=canonical][href]` 指向 `/`，`a[href]` 包含 `/channel/tv`、`/channel/movie` 等同主机频道路径 | 高：桌面公开入口及同主机页面；不代表播放器 API 或音频/视频 CDN |
| `m.v.qq.com` | [桌面官网](https://v.qq.com/)及[移动官网入口](https://m.v.qq.com/x/m/channel/figure/index) | 桌面 HTML 的 `link[rel=alternate][href]` 指向 `/x/m/channel/figure/index`；该移动页实际读取 HTTP 200、标题标识腾讯视频，并有 `link[rel=canonical]` 同路径和 `a[href]` 的 `/hippysearch/index.html` | 高：移动网页公开入口；未执行搜索，不推断原生 App 请求 |
| `film.qq.com` | [桌面官网](https://v.qq.com/)及[公开会员旧入口](https://film.qq.com/) | 桌面 HTML 的 `a[href]` 指向该主机 `/`；独立读取重定向头为 HTTP 302，目的主机 `film.video.qq.com`、路径 `/` | 高：官网实际关联的会员入口别名；只核实这一跳，不推断未知重定向或购买链路 |
| `film.video.qq.com` | [公开会员页](https://film.video.qq.com/)，由[官网关联入口](https://film.qq.com/)跳转到达 | 最终页面 HTTP 200，标题标识腾讯视频 VIP；真实 `script[src]` 为 `/lib/shortcache/vft-lib/js/storage.min.js`，`link[rel=stylesheet][href]` 为 `/lib/midcache/web-base/vip-web-base.css` | 高：公开会员页及同主机脚本/样式；移动页也引用其公开登录模块脚本，但未执行账号操作、不证明认证/支付全链路 |

置信度指“官方页面确实使用或链接该精确主机”的证据，不是服务独占性、全部地区可达性、版权资格或完整功能审计。
同一主机的所有路径都会跟随该组，包括同主机会员、推广、其他频道或脚本；主机规则无法按路径区分。
例如桌面站还有 `/channel/game_new` 等频道路径；不据此添加独立游戏主机，也不承诺能把同一主机中的某个频道排除在外。

## 有实际引用但仍排除的共享 / 非目标范围

| 主机或范围 | 官方页面观察 | 排除理由 |
| --- | --- | --- |
| `qq.com`、`gtimg.cn`、`gtimg.com`、`qpic.cn` 等根域及整根后缀 | 多个腾讯业务共享的命名空间 | 不以腾讯所有权或站点资源引用为理由扩大根域 |
| `vfiles.gtimg.cn` | 桌面官网真实 `script[src]`：`/tvideo2/channel-vue/assets/index-DXL4nLVV.js`；`img[src]`：`/tvideo2/channel-vue/assets/logo-Ckf4UreJ.svg` | 已证明视频页面使用这些路径，未证明整个共享 CDN 主机的专属边界；首批仅入口控制，默认排除，若要纳入需单独审范围 |
| `vm.gtimg.cn`、`midas.gtimg.cn` | 移动页真实 `script[src]`：`/thumbplayer/superplayer/superplayer.js`、`/h5pay/js/api/midas.js` | 播放器/支付公共模块的使用证据不等于视频专属服务；不为补齐功能扩大共享主机 |
| `tv.puui.qpic.cn`、`puui.qpic.cn` | 桌面/移动 HTML 的实际 `img[src]`，路径分别位于 `/tv/`、`/vupload/` | 仅证明页面使用部分图片；首批不纳入图片 CDN，不承诺封面完整覆盖 |
| `pbaccess.video.qq.com`、`video.qq.com`、`vd6.l.qq.com` | 首页或移动页 `link[rel=preconnect]`，不是实际接口请求 | 预连接不能证明必要业务或播放链路，不据命名补齐 API |
| `staticfile.qq.com`、`res.ab.qq.com`、`config.ab.qq.com` | 移动页可见 `/datong/universalReportH5/`、`/tab/` 下脚本；部分仅预取/预连接 | 公开上报/实验模块或配置候选，不作为核心功能扩充；不把其一概宣称为当前 Privacy 已拦截 |
| `dcm.qq.com`、`dldir1.qq.com` 等腾讯下载控制 / 共享下载候选 | 会员页有 `a[href]` 指向 `dcm.qq.com/txsp.html`；未读取安装包，未核实后续目的 | 不能从一个产品下载链接推断整个下载主机专属；未知重定向目的也不纳入 |
| `iwan.video.qq.com`、`iwan.qq.com`、`iwan-s.video.qq.com` | 桌面/会员页链接有 `/redirect_to_legend_hall`、`/game-community/game-center/home`，另有 DNS 预取 | 游戏入口或线索不是本轮视频分流范围，保留原策略 |
| `cc.v.qq.com`、`mp.v.qq.com` | 会员页还链接这些主机，但未核实它们的业务页面 | 不能把所有同厂商或同父域入口自动纳入 |
| 其他追踪主机、直播服务、爱奇艺/优酷、QQ 音乐、腾讯游戏及未观察的播放/鉴权接口 | 非目标或证据不足 | 不猜测，不采集私人流量补齐，不改变已有独立服务控制 |

排除不等于这些主机没有作用或不属于腾讯视频；仅表示本轮精确范围不覆盖。
有的公开页面会依赖被排除的资源，因此“4 个入口可独立选择出口”不能解释为“页面、下载或播放将全部走同一出口”。

## 基线 first-match 核实

基线 `a1c2dd26337b7277019a8764785cdf258bb6f045`，41 项服务 / 288 tests。
该提交的 Git tree 与已验证的 QQ 音乐整合提交 `da045c866cd02ee1b0ab90d9461f6b74b5693ab8` 相同，已有验证证据可复用。
本次另读取公开 manifests 与 `config/rules.yaml`，使用现有 `siri_ai.DomainRules`、`entries` 按实际规则顺序进行域名首匹配模拟：

| 目标 / 负向对照 | 当前首条命中 |
| --- | --- |
| 上述 4 个拟纳入主机 | `ChinaMax` → `🇨🇳 China-Global` |
| `y.qq.com`、`c.y.qq.com`、`dldir.y.qq.com` | `QQMusic` → `🎧 QQ 音乐` |
| `game.qq.com`、`wegame.gtimg.com` | `ChinaGaming` → `DIRECT` |
| `iwan.video.qq.com`、`iwan-s.video.qq.com`、`iwan.qq.com` | `ChinaMax` → `🇨🇳 China-Global`，本轮不得改归视频组 |
| 上表已模拟的共享 CDN、图片、下载候选及仅预连接接口 | `ChinaMax` → `🇨🇳 China-Global` |
| `live.qq.com`、`www.iqiyi.com`、`www.youku.com` | `ChinaMax` → `🇨🇳 China-Global`；仅作未纳入对照，不宣称本次观察到它们的请求 |
| `stat.y.qq.com` | `Privacy` → `REJECT` |
| `child.v.qq.com`、`notv.qq.com` | `ChinaMax` → `🇨🇳 China-Global` |
| `v.qq.com.example.org`、`example.org` | `MATCH` → `🧭 Final` |

当前没有更早的安全、游戏或既有 App 提前命中四个目标。新增位置建议在既有 App（包括 QQMusic、Taobao）之后、SiriAI / Apple / GlobalMedia / GEOIP CN / ChinaMax 之前，不挪动原有规则。
必须保持 reject/security 优先、InternationalGaming → ChinaGaming、SiriAI → Apple 及 FINAL/MATCH 语义。
本模型没有 IP、进程或端口元数据，不是完整 Mihomo 请求或真实出口实测；生产验证拟拒绝新引用前出现任何顶层 GEOIP/IP-CIDR/IP-CIDR6，未知顶层条件也应明确拒绝。

## 最小实施提案（待审查，不在本提交实施）

目标：仅为 4 个官方公开入口主机提供独立、默认直连的手动出口选择，不扩展共享服务、不承诺完整视频功能。

1. 新增固定 4 条 `DOMAIN` 的 `TencentVideo` provider、服务登记及 `📺 腾讯视频` select 组；首项 DIRECT，包含手动 `🚀 节点选择`。一次 active 引用按前述位置放置，既有配置、Siri、安全和游戏路由保持。
2. 新增 `validate_tencent_video(root)` 并接入 `validate_tree(root)`。复用已合入的 `app_policy.validate_select_group`，不另写 type 正则或模拟通用 YAML，不改共享组件或旧 App。
3. 生产门禁固定范围和重复、唯一有效引用、所需顺序标记、DIRECT-first / 手动代理、manifest 同名冲突和未知/缺失 provider、未知顶层规则及前置 IP 条件。未来合法 Privacy/REJECT 或 Hijacking/🚫 Hijacking 抢先命中应继续通过，非安全抢占和错误 target 应拒绝。
4. 新增独立固定 HOSTS、QQMusic / TencentGames / 共享域 / 其他视频品牌负控；逐目标检查子域、相似前缀与伪后缀。真实公共 fixture mutation 实调 helper 和完整 tree，覆盖范围、引用、顺序、默认、复杂 type/proxies YAML、合法 select 形式、IP/未知类型、provider 和安全更新；文本读写显式 UTF-8。
5. 目录写明“部分公开入口：默认直连，可选代理”，不把共享资源或播放接口算入覆盖。按已有 generator 离线生成资产，跑完整 tests、validate、public_check、生成一致性及 diff 检查；不运行网络同步、不改权限/工作流。

预计涉及 provider、local manifest、catalog 登记、策略组/有序规则、新 App validator/测试、研究及相应生成资产；本分支顺序实施，不在共享工作树并写。
主要风险为同主机全路径影响和 mixed-egress；以明确范围、负控、首匹配验证和独立审查约束。若只有整根共享规则才能继续，应减小范围或停止，不以 broad suffix 代替证据。
非目标：登录、购买、版权或地区资格解锁、播放/CDN 全链路、原生 App 覆盖、账号风控实测、其他腾讯产品及旧 App 重构。

## English scope summary

Research only; implementation awaits approval. The proposed scope is four exact public entry hosts: `v.qq.com`, `m.v.qq.com`, `film.qq.com`, and `film.video.qq.com`.
Official desktop/mobile HTML, a public 302 redirect, and actual same-host script/stylesheet declarations provide the evidence; no account, playback, purchase, installer download, or private traffic was used.
The proposed group defaults to DIRECT with an optional manual proxy. All paths on each listed host are affected, but shared Tencent CDN/download hosts, games, other streaming brands, and preconnect-only API candidates remain excluded.
Unlisted resources, player APIs and media requests retain their original routes, so mixed egress is possible. This is not complete website/native-app/playback coverage or copyright/region unlocking.
Implementation must reuse the existing restricted public-template policy guard, preserve security/gaming and QQ Music controls, and pass real helper/full-tree mutation tests without changing permissions or workflows.
