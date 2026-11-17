# 优酷公开入口精确分流研究

## 状态与最小建议

`RESEARCHING`：本提交仅保存公开证据与实施建议，尚未新增 provider、策略组或路由，等待范围批准。

建议首批仅纳入 **1 个精确主机：`www.youku.com`**，provider `Youku`、目录 id `youku`，独立策略 `🎞️ 优酷`，默认 `DIRECT`，可选 `🚀 节点选择` 与 `🧭 Final`。
这提供的是官网、同主机个人中心公开外壳和客户端介绍页的独立出口选择，不是完整网站、原生 App、安装包、账号或视频播放链路覆盖。
现有 ChinaMax 已覆盖该主机；新增价值是单独控制出口，而不是修复一个已证明的播放故障。

## 官方公开证据

核实日期：2026-11-17。仅匿名读取官方公开 HTML；未登录、购买、播放、获取安装包或采集私人流量，不读取私人配置、凭据或订阅。
网页提取与直接 HTTPS 读取交叉核对；记录只保留公开主机、标签和去除查询参数的路径，不保存原始页面、会话或查询值。
页面内容可能动态变化；下述事实证明公开页面声明的关联，不代表浏览器已执行脚本或加载全部资源。

| 拟纳入精确主机 | Primary source | 实际观察 | 用途 / 置信度 / 影响 |
| --- | --- | --- | --- |
| `www.youku.com` | [优酷官网](https://www.youku.com/) | 匿名读取 HTTP 200；标题“优酷-热门独播剧集综艺电影在线观看-为好内容全力以赴”；真实 `a[href]` 同主机路径 `/`，导航包含首页、电视剧、动漫、电影、综艺、会员中心等 | 高：官网公开入口，不能据导航文字证明频道或播放成功；同主机全部路径都会受该组控制 |
| 同上，不增加主机 | [公开个人中心入口](https://www.youku.com/ku/usc/index) | HTML 标题“优酷 - 为好内容全力以赴”；真实 `a[href]` 指向同主机 `/ku/profile/index`、`/ku/profile/subscribe`、`/ku/usc/card`、`/ku/usc/creation`、`/ku/usc/fav`；页面有登录提示 / 占位内容 | 高：官方公开外壳和导航存在；未执行登录、读取用户资料或核实账户功能 |
| 同上，不增加主机 | [客户端介绍页](https://www.youku.com/ku/product/index) | HTML 展示 Windows、Mac、Harmony 及桌面 / 手机 / 平板 / TV / 车载分类；实际样式和脚本声明位于 `g.alicdn.com` 的 `/youku-node/pc-pages-v2/4.1.90/v2/static/css/ProductPage.chunk.css`、`/static/js/ProductPage.chunk.js` 等路径 | 高：官网客户端介绍外壳；共享静态资源不纳入，也未跟随下载或验证安装包目的主机 |

置信度仅针对“该主机是官方公开入口并存在这些声明”，不是全部功能、地区可达性或服务专属性的保证。
精确 DOMAIN 也无法按路径细分：同主机会员、登录提示、直播 / 游戏导航、推广或未来新增路径均随该组出口，不承诺排除其中某个路径。

## 观察到但本批不纳入的范围

| 主机 / 范围 | 公开观察或证据边界 | 排除理由 |
| --- | --- | --- |
| `g.alicdn.com` | 个人中心 / 客户端页实际 `link[rel=stylesheet]`、`script[src]`；除了页面脚本，还见 `/scout/probe_cdn/index.js`、`/kplayer/adreport/…/index.js`；客户端页还引用 `/youkuvip_fe/vip-public-assets/pay/pay.js` | 阿里共享 CDN；页面路径、支付模块或广告上报的使用证据，不足以把整个主机划给优酷 |
| `img.alicdn.com`、`gw.alicdn.com` | 三个页面真实 `img[src]`，个人中心 favicon 也在 `img.alicdn.com/imgextra/` | 共享图片主机，不因部分图片被优酷使用而整主机纳入 |
| `ykimg.alicdn.com`、`liangcang-material.alicdn.com` | 首页真实 `img[src]`，路径分别如 `/develop/image/…`、`/prod/ued/upload/…` | 已观察部分图片引用，未证明整主机专属范围；首批不覆盖图片链路 |
| `qzs.gdtimg.com` | 首页及个人中心真实 `script[src]`：`/union/res/pc/ylh-pc-ad-sdk.v1.20.20.js` | 广告 SDK，不作为核心入口扩充；不能据脚本名宣称它已被当前 Privacy 拦截 |
| `v.youku.com` | 首页一次匿名 HTML 中有真实 `a[href]` 指向该主机 `/video`；未跟随原链接验证视频页或执行播放器 | 仅保留为公开候选，本批先缩小到已实际读取的官网入口；不据命名或链接猜测播放接口 / 必需依赖，也不以缺少原参数的路径探测判断视频页是否可用 |
| `t.youku.com` | 首页真实 `a[href]` 指向 `/yep/page/pc/6tvjgjm2md` 等活动路径 | 活动 / 营销页面不自动并入入口控制，不推断整个主机的其他用途 |
| `jingrui-ai-competition.youku.com`、`acg.youku.com` | 首页分别有真实赛事 `a[href]` 与 `/webfile/` 下 `img[src]` | 独立赛事 / 内容资源候选；非本轮官网入口范围，所有权关联不等于纳入依据 |
| `wy.668wan.com` | 首页真实 `a[href]`：`/wztx/SH7gAk/index.html` | 外部游戏入口，本轮不改游戏业务路由 |
| `youku.com`、`ykimg.com`、`alicdn.com`、`aliyun.com` 等整根后缀 | 未建立整个命名空间属于本轮入口范围的证据 | 禁止扩大根域、共享 CDN、其他业务或海外平台 |
| `m.youku.com`、`www.youku.tv`、`www.kumiao.com`、未知 API / 鉴权 / 下载 / 媒体主机 | 本轮未取得可支持纳入的实际公开页面 / 资源证据；仅作为负向边界，不声称它们均已被官网引用 | 不猜移动接口、国际站、酷喵、播放器或 App 后端；不从 DNS 预取、脚本字符串或所属公司推导功能覆盖 |

排除不意味着这些主机没有作用或不属于相关业务，只表示本次不改变其路由。
页面已明确使用被排除的静态 / 图片资源，所以即便为 `www.youku.com` 手动选择代理，也会出现 mixed-egress：其他主机保留原策略，不能把“入口可选代理”解释成全站、登录或播放统一出口。
如切代理后出现登录、地区识别或页面异常，可恢复默认直连；这是混合出口的条件性风险提示，不是已实测的风控结论。
出口选择不能解锁会员资格、版权、地区、账号或设备限制。

## 当前 first-match 与回归边界

基线 `3ee79fedd218dc178efd91251d7fbf48ca2b8b17`，45 项服务 / 402 tests；完整 tests 使用该精确基线已有通过证据，本次研究另跑默认检查。
只读取公共 manifests、ruleset 与有序配置，使用现有 `siri_ai.DomainRules` / `entries` 按实际顺序模拟：

| 目标 / 对照 | 当前首条命中 |
| --- | --- |
| `www.youku.com` | `ChinaMax` → `🇨🇳 China-Global` |
| `youku.com`、`m.youku.com`、`v.youku.com`、`t.youku.com`、`acg.youku.com`、`jingrui-ai-competition.youku.com` | `ChinaMax` → `🇨🇳 China-Global` |
| 上表的五个具体 `alicdn.com` 资源主机、`wy.668wan.com`、`www.kumiao.com` | `ChinaMax` → `🇨🇳 China-Global` |
| `qzs.gdtimg.com`、`www.youku.tv` | `MATCH` → `🧭 Final` |
| `www.taobao.com`、`www.alipan.com`、`v.qq.com`、`www.kuaishou.com` | 分别为 `Taobao`、`AliPan`、`TencentVideo`、`Kuaishou` 的独立组 |
| `game.qq.com` | `ChinaGaming` → `DIRECT` |
| `guzzoni.apple.com` | `SiriAI` → `🤖 AI 服务` |
| `child.www.youku.com`、`notwww.youku.com` | `ChinaMax` → `🇨🇳 China-Global` |
| `www.youku.com.example.org`、`example.org` | `MATCH` → `🧭 Final` |

当前更早的安全、游戏和既有 App 未抢占目标；这是逐项实际匹配结果，不假设旧 provider 都使用 exact DOMAIN。
未来合法 `Privacy` → `REJECT` 或 `Hijacking` → `🚫 Hijacking` 应继续优先，不能为了让入口命中而绕过安全规则。
模型只有域名，没有 IP、进程、端口等元数据，不是完整 Mihomo、DNS、GeoIP、UDP 或真实出口 / 播放实测。

## 待批准的最小实施计划

目标：一个官网精确主机的独立、默认直连出口控制。非目标：完整 App / 播放 / 下载 / 登录 / 支付链路、会员版权地区解锁、国际站、共享资源、游戏及旧 App 重构。

1. 新增仅 `DOMAIN,www.youku.com` 的 `Youku` provider、local manifest、catalog 服务与 `🎞️ 优酷` select 组；DIRECT-first，包含手动代理和 Final。目录标题 / 标签明确“部分公开入口”，警告明确只有一个已列主机，其他资源与视频页仍走原策略。
2. 唯一 active `RULE-SET,Youku,🎞️ 优酷` 放在全部 17 个已合 App 之后、SiriAI 之前。前驱固定包括 QQMusic、Douyin、Amap、Zhihu、Xiaohongshu、NetEaseMusic、Douban、JD、Meituan、BaiduPan、Ctrip、Pinduoduo、Taobao、BaiduMap、Kuaishou、TencentVideo、AliPan；同时保留 Privacy / Hijacking → InternationalGaming → ChinaGaming 优先。后继固定 SiriAI、Apple、YouTube、Bilibili、TikTok、Disney、Netflix、GlobalMedia、GEOIP CN 和 ChinaMax；不挪动既有规则、FINAL 或 MATCH。
3. 新增 `validate_youku(root)` 并通过真实 `validate_tree(root)` 接入。复用已合 `app_policy.validate_select_group` 的受限公共模板语法，不是通用 YAML / 私人配置解析器；共享组件和全部旧 App 保持不变。门禁固定 exact 范围 / 重复、引用唯一、顺序锚点、DIRECT / 代理 / Final、manifest provider collision 与缺失 provider 的明确诊断。未知顶层条件及目标前的 GEOIP / IP-CIDR / IP-CIDR6 明确 fail-closed，不跳过域名模型无法验证的前置条件。
4. 新测试使用独立固定 HOSTS 与固定排除对照，逐目标验证子域、相似前缀和伪后缀。真实临时公共 fixture 调用 helper 和完整 tree，覆盖未变异成功、范围扩大、重复、引用 / 顺序 / 默认 / 缺 Final、复杂 type/proxies key / tag / anchor / escape / merge、合法 select 格式、provider collision / missing、UTF-8、未知 / IP 条件，以及合法安全命中成功、非安全抢占 / 错 target 拒绝。负向流量在加入该 provider 前后必须不变。
5. 修改 canonical 输入后只用已有离线 generator 重建派生文件；跑专项与完整 tests、validate、public_check、生成一致性和 diff 检查，再交独立审查。不得运行网络同步、改权限 / workflow / shared parser / 旧 App，或手改生成资产。

预期涉及 `ruleset/Youku.yaml`、`local-rulesets.json`、`catalog/services.json`、`config/`、新 validator / 测试、本研究和 generator 声明的派生文件。实施风险主要是同主机全路径与混合出口，以上述明确范围、负控及真实首匹配门禁约束；如证据不足应继续缩小范围而非增加共享后缀。

## 本次验证与安全记录

- `scripts/validate.py`：45 services、24 mirrored / 21 local，生成 / hash / provider / 文档一致性通过。
- `scripts/public_check.py`：172 个公共文件通过；`git diff --check` 通过。
- 只新增本研究文档，没有生产、权限、工作流、共享组件或旧 App 变更；未执行 push、PR、merge、sync、reset、restore、clean 或 stash。

## English scope summary

Research-only proposal: one exact public entry host, `www.youku.com`, with a DIRECT-first `🎞️ 优酷` group and optional manual proxy / Final. Official homepage, public account-shell and product-page HTML establish the entry; no login, purchase, playback, installer or private traffic was used.
All paths on this host would follow the group, including same-host promotional or account-related paths. Shared Alibaba assets, observed advertising / campaign / game hosts, the unverified video-page candidate, overseas services and unknown APIs remain excluded. Mixed egress is expected; this is not complete website, native-app, account, download or playback coverage, and does not unlock membership, copyright or regional eligibility.
Implementation awaits scope approval. It must preserve all 17 existing App routes plus security / gaming priority, reuse the unchanged restricted public-template policy guard, and pass real helper / full-tree mutations without permission or workflow changes.
