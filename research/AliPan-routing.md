# 阿里云盘公开入口精确分流依据

## 已核实候选与决策边界

核实日期：2026-11-16。最小方案仅为 `www.alipan.com` 和 `www.aliyundrive.com` 两个精确 `DOMAIN` 提供独立 `📁 阿里云盘` 策略，默认直连，可手动选择代理。两者在基线 `a1c2dd26337b7277019a8764785cdf258bb6f045` 都已由 `ChinaMax → 🇨🇳 China-Global` 覆盖，新增价值是独立出口控制，不是此前完全没有规则。

只匿名读取公开首页、下载页和官方声明，未登录、不携带浏览器 Cookie、不请求任何实际分享链接、账户、文件或下载二进制。原始响应必须按服务器协商正常解压：本次使用标准 `curl --compressed` 后可取得下表标题及资源标签；未解压的正文不可读不被当成验证失败或绕过理由。

| 精确主机 | 官方公开来源与观察 | 用途、目标与置信度 |
| --- | --- | --- |
| `www.alipan.com` | [官网](https://www.alipan.com/)及[下载页](https://www.alipan.com/download)实际 HTML 标题均标识阿里云盘和阿里巴巴集团；[服务协议](https://www.alipan.com/protocol/service)也将该主机列为官网 | 当前公开入口；默认直连，可选代理。高：入口身份与公开内容证据，不代表账户或文件功能实测 |
| `www.aliyundrive.com` | [兼容入口](https://www.aliyundrive.com/)实际 HTML 返回同一品牌标题；[该主机的服务协议](https://www.aliyundrive.com/protocol/service)与[隐私政策](https://www.aliyundrive.com/protocol/private)标识同一服务；[开发者 App Store 页面](https://apps.apple.com/cn/app/id1494661473)也公开引用此主机的隐私政策 | 官方兼容公开入口；默认直连，可选代理。高：只证明此入口与产品关联；本次没有将它描述为已核实的重定向链或完整旧版客户端支持 |

只记录主机和无查询参数的公开来源，不保存原始网页、响应头、签名链接或其中可能出现的临时字段。App Store 证据是开发者提供的产品元数据，不代表平台独立审计了主机所有权或可用性。

## 资源与候选排除

官网实际 `script[src]` / `link[href]` 引用 `g.alicdn.com` 上 `/aliyun-drive-fe/aliyun-drive-home/` 的资源及统计脚本，也引用 `img.alicdn.com` 图标。它们都是广泛共享主机，不能仅凭路径把整个主机认定为云盘专属，本批不加入。

公开 HTML 还包含 `api.aliyundrive.com`、`auth.aliyundrive.com`、`cdn.aliyundrive.net`、`pages.aliyundrive.com`、`stg.aliyundrive.com`、`appdownload.alicdn.com` 以及日志/上报主机的字符串。本次没有把配置、白名单或仅声明字符串当作实际必要请求证据，不纳入 API、认证、CDN、页面分发、测试环境、下载或统计覆盖。也不猜测 `api.alipan.com`、开放平台或 OSS 的端点。

不使用 `alipan.com`、`aliyundrive.com`、`aliyundrive.net`、`alicdn.com` 或任何云存储域名的后缀。两个不带 `www` 的根主机本身也不在正式清单内；其他客户端、API、登录或分享入口继续沿原路由。阿里云、淘宝、钉钉、其他网盘及国际服务不改归本组。已有与未来合法 Privacy/Hijacking 拦截仍优先。

## 最小实施提案（待独立方案审查）

1. 仅新增 `AliPan` / `alipan` 的两条固定 `DOMAIN`、本地登记与目录说明；独立 `📁 阿里云盘` 为唯一 `select` 组，`DIRECT` 首选并保留手动代理和 Final 选项。
2. 只添加一个活动引用，位于既有安全、游戏、APP 规则之后，SiriAI/Apple/国际媒体/GeoIP/ChinaMax 等更宽规则之前；不重排已合规则。
3. 增加 `validate_alipan(root)` 与真实 `validate_tree` 门禁，复用现成 `app_policy.validate_select_group` 的受限公共模板语法，不修改旧 APP 或共享组件。检查固定范围、重复、活动引用与必要顺序、默认与可选出口、缺失/冲突 provider 的明确错误、UTF-8，以及真实域名首匹配和非目标不变。
4. 域名模型不拥有 IP/进程元数据：前置 IP/GeoIP 条件不能被静默当作未命中，应明确拒绝；未知顶层规则也 fail-closed。正确安全拦截可优先，非安全抢占或错误安全目标拒绝。
5. 临时公开 fixture 中实际调用 helper 和完整树，覆盖范围/重复/引用/顺序/策略、合法安全更新、遮蔽、未知 provider/规则、前置 IP、UTF-8、复杂 YAML 键及 proxies 覆盖；独立固定 HOSTS 与根域/相似子域/API/认证/CDN/日志/其他 APP 负向对照。仅跑离线现成生成器，再全量 tests、validate、public_check、生成一致性、diff 检查。

## 使用限制

这是两个公开入口的独立出口，不是原生 APP、登录、上传、下载、文件内容、同步或分享全链路规则。主机级规则影响这两个主机上的全部路径，不能只改变首页；未列出的主机继续原路由，可能形成混合出口。切到代理后若出现登录或地区识别异常，可恢复 DIRECT 排查，这只是条件性建议，不是已实测的风控结论。规则不改变账号、会员、容量、传输速度或地区资格。

实际 DNS、GeoIP、UDP、文件传输或账户行为未实测。没有通过访问私人配置、抓包、令牌或登录态补足范围，也不鼓励在 issue 中上传这些数据。

## English scope summary

Only two exact official public entry hosts are proposed: `www.alipan.com` and `www.aliyundrive.com`. They already match ChinaMax; a DIRECT-first optional policy adds independent control. Shared Alibaba CDNs and unobserved API/auth/storage/download endpoints stay out. This is not full native-app, account or file-transfer coverage. Each host includes all paths; other traffic retains its route and mixed egress is possible. Public pages were fetched anonymously with normal response decompression, without login, private links, tokens or file access.
