# 夸克公开门户精确分流依据

核实日期：2026-11-18。基线：`74b4640cfb0d8cef4395fb199f8e9f8903fcd84e`。

## 官方证据与建议范围

只匿名读取公开介绍和门户，不登录、上传、搜索账户内容、播放或请求安装包。以下是域名归类依据，不是账号、服务可用性或完整客户端流量证明。

| 精确主机 | 主源与核实方式 | 用途、目标、置信度与影响 |
| --- | --- | --- |
| `www.quark.cn` | [夸克官网](https://www.quark.cn/)展示浏览器及网盘产品；[国内 App Store 的开发者说明](https://apps.apple.com/cn/app/id1160172628)声明同一官网并介绍网盘功能 | 官网公开门户；高置信产品入口。默认 `DIRECT`，可选现有代理与 Final；同主机全部路径跟随，不区分宣传、账户外壳或其他产品路径。开发者声明不等于 Apple 独立认证 |
| `pan.quark.cn` | 官网“夸克网盘”实际链接指向[此门户](https://pan.quark.cn/)；网页提取工具超时，另一次普通匿名 HTTPS GET 返回 200、仍在同主机，页面标题识别为夸克网盘 | 官网声明的网盘入口，并有公开页面响应交叉核实；高置信入口，不代表认证、传输或原生客户端端点。默认 `DIRECT`，可选代理与 Final；包括同主机全部路径 |

基线实际有序域名模型中，两个主机均为 `ChinaMax → 🇨🇳 China-Global`。新增策略提供独立出口控制，不是首次覆盖，也不证明旧连接有故障；ChinaMax 是可选策略，不能据此推断用户私人配置当前选了哪个出口。

## 排除与使用限制

- 只建议两个精确 `DOMAIN`，不添加整个 `quark.cn`、`sm.cn`、`alicdn.com` 或其他共享根域后缀。
- 官网声明的共享素材主机 `img.alicdn.com`、`g.alicdn.com`、`blm.sm.cn` 不纳入。`scan.quark.cn` 的扫描王入口、`talent.quark.cn` 招聘入口及历史 / HD 入口 `www.myquark.cn` 也不在本批；没有否认其品牌关联，只是不扩本次范围。
- 不猜测搜索、千问 / AI、登录、鉴权、会员、文件 API、上传下载或传输 CDN。未核实的接口外形只能作为负向边界测试，不能伪装为本轮观察到的官方请求。
- 同主机全路径都随策略，不能按页面、产品、用户或 URL 路径隔离；其他主机仍走原策略，手动代理可能形成混合出口。切换后如遇会话或地区异常，可恢复 DIRECT 排查；未实测风控效果。
- 不保证原生 App、浏览任意网站、AI、登录、网盘上传下载、同步、分享、播放或安装包链路；不解锁账号、付费、地区资格或速度。未实测 DNS、GeoIP、IP / 进程元数据、代理连通性或真实客户端。

## 接入与验证合约

建议 provider `Quark`、目录 id `quark`、分类“工具”，独立 `🔍 夸克` literal select：DIRECT-first，加上现有 `🚀 节点选择` 和 `🧭 Final`。只在 21 个既有 App（含 Youku）之后、Siri AI 之前新增一个引用；保留全部旧规则相对顺序、安全与游戏优先、Gemini 在 Google 前及原 MATCH。

仅新增 `validate_quark(root)` 与一次 tree 调用，复用未改变的结构读取和策略组选项合同。验收覆盖固定两个主机及非目标对照、实际首匹配、合法安全更新、非安全抢先、未知 / 不完整 / 空白字段 / 前置 IP、provider 缺失和冲突、UTF-8、重复根键及真实完整公共 fixture 正向与变异。直接 helper 必须给出严格自身错误；完整树允许更早门禁以准确原因拒绝，不把“必须最后由夸克报错”作为合同。

不改旧校验函数、共享模块、镜像、来源锁、依赖、工作流或权限。派生目录、provider 与散列只通过现有离线生成器维护。

## English scope summary

Proposed scope: two exact public entry hosts, `www.quark.cn` and `pan.quark.cn`. The official homepage links the cloud-drive portal, and the developer's Chinese App Store description declares the website and cloud-drive feature. An anonymous portal GET also returned HTTP 200 on the same host after the page extractor timed out. This establishes public entry attribution, not complete network coverage or service availability.

All paths on these two hosts follow an optional DIRECT-first group. Shared Alibaba / Shenma resources, scan/recruitment/legacy hosts, and unverified search, AI, authentication or file-transfer hosts remain excluded. Other traffic retains its routing and may use a different exit. No login, upload, playback, download, native-client, account, entitlement, speed or regional guarantee is made; existing security, game and App precedence remains unchanged.
