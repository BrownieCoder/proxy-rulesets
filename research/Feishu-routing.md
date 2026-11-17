# 飞书公开入口精确分流研究

## 决定与状态

核实日期：2026-11-18。已接受并落实首批仅收录 **`DOMAIN,www.feishu.cn` 一条规则**，provider `Feishu`、服务 id `feishu`、分类“办公”，独立策略 `💼 飞书` 默认 `DIRECT`，保留 `🚀 节点选择` 和 `🧭 Final`。原始研究作为独立历史提交保留；以下记录最终范围及验证约定。

它提供的是一个官方公开声明/网站入口主机的独立选择，不是首次覆盖或完整飞书 App 分流。基线 `74b4640cfb0d8cef4395fb199f8e9f8903fcd84e` 已将该主机交给 `ChinaMax → 🇨🇳 China-Global`。

## 官方证据与置信度

只匿名读取国内 App Store 开发者元数据与官方公开页面，不携带现有 Cookie，不执行脚本，不点击登录、客户端下载文件或企业空间。只保留公开来源、主机及去查询参数的路径，不保存网页原文、响应头、账户字段或企业内容。

| 候选精确主机 | Primary source 与实际观察 | 用途、置信度及限制 |
| --- | --- | --- |
| `www.feishu.cn` | [国内版飞书 App Store 页面](https://apps.apple.com/cn/app/id1401729613)标识飞书及开发者 Beijing Feishu Technology Co., Ltd.；开发者隐私政策是真实链接，目标为[同主机 `/privacy`](https://www.feishu.cn/privacy)，实际打开后网页标题为“飞书隐私政策”。开发者提供的应用说明另明确列出同主机 `/terms` 与 `/privacy`；后二者在说明中的文字地址不冒充新资源抓取 | 高：官方开发者声明及隐私页面入口的身份关联。不是 Apple 对主机独占性、资格或功能可用性的认证；隐私页没有可读正文，不声称已解析其中的资源或业务接口 |
| 同上，不新增主机 | [官方客户端下载介绍页](https://www.feishu.cn/download)的网页标题为“下载飞书 App 及桌面客户端 - 飞书官网”；[官方客户端下载帮助文章](https://www.feishu.cn/hc/zh-CN/articles/360025035993)落在同一主机的中文文章路径，标题标识“下载和安装飞书客户端” | 支持同一官网/帮助入口的关联。网页读取没有提供可读正文，未提取真实安装包或资源标签；没有点击下载，不从页面标题猜测下载/CDN/API 域名 |
| 同上，但必须说明跨主机跳转 | [官网首页](https://www.feishu.cn/)在本次网页读取中最终转到 `www.larksuite.com` 的 `/en_sg/` 页面 | 当前观察存在地区相关的跨主机跳转；不能以跳转后的国际站内容为飞书国内服务资源证据。未取得可读正文，也未据此推断跳转状态码、所有地区行为或服务器的具体判断机制 |

一次独立匿名 HTTPS 交叉读取因本环境 DNS 解析失败，未取得 HTTP 响应；不把本地失败写成站点失效、HTTP 状态或业务故障。现有证据足以支持一个由国内 App 开发者实际声明的精确主机，不足以支持更多接口、共享资源或原生 App 链路。

## 跳转、全路径与排除边界

`DOMAIN,www.feishu.cn` 影响该主机的全部路径，包括官网、帮助、条款、隐私及将来同主机的登录、推广、脚本或其他内容；规则不能只控制首页或按路径剥离统计请求。

当前观察到的国际跳转目标 **`www.larksuite.com` 不纳入**，`larksuite.com` 裸根也仅作为负向边界，不从产品关联扩大到国际版。请求跳转后仍沿原策略，可能形成混合出口；为一个入口选择代理不等于控制跳转后整站，也不保证保持国内版页面或避免地区跳转。

不增加 `DOMAIN-SUFFIX,feishu.cn`、裸根 `feishu.cn`、任意租户子域或通配符；不猜测文档、聊天、会议、鉴权、开放平台 API、文件传输、安装包和遥测主机，不归入共享字节跳动/云/CDN 根域。其他产品及国际版保持原规则。没有访问企业租户、私人文档、日历、联系人、消息或会议。

## 基线首匹配与负控

只读取公开 manifests、规则与 `config/rules.yaml`，按现有 `DomainRules` 进行没有 IP/进程/端口元数据的域名模拟：

| 对象 | 基线首匹配 |
| --- | --- |
| `www.feishu.cn`、`feishu.cn` | `ChinaMax → 🇨🇳 China-Global` |
| `www.larksuite.com`、`larksuite.com` | `ChinaMax → 🇨🇳 China-Global`；沿用它们的现有策略，不因“国际版”字样擅自改路由 |
| `apps.apple.com` | `Apple → 🍎 Apple` |
| `child.www.feishu.cn`、`notwww.feishu.cn` | `ChinaMax → 🇨🇳 China-Global`；仅为命名负控，未查询其存在性 |
| `www.feishu.cn.example.org`、`example.org` | `MATCH → 🧭 Final` |
| `www.iqiyi.com`、`www.youku.com`、`www.goofish.com`、`www.12306.cn` | 分别保持 `IQIYI`、`Youku`、`Xianyu`、`Railway12306` 独立策略 |
| `guzzoni.apple.com`、`msg.qy.net`、`fastcdn.hoyoverse.com` | 分别为 `SiriAI`、`Privacy → REJECT`、既有 exact `DOMAIN → DIRECT` |

后续须独立固定 `HOSTS = {'www.feishu.cn'}` 与完整负控集合，覆盖上述根域、国际跳转、伪子域边界、旧 App/Apple/Siri/游戏/隐私及非目标服务；对负控比较启用/移除此新 provider 的首匹配，结果必须不变。不能硬编码跳过 ChinaMax，未来合法 Privacy/Hijacking 抢先命中仍须通过同一验收路径。

## 已落实范围与验证约定

目标：单个公开入口的独立可选出口。非目标：完整网站或原生客户端、登录、企业空间、文档编辑、IM、会议、API、下载链路、地区资格或功能故障修复。

1. 只增加一条固定 exact 规则、本地 manifest、`💼 飞书` DIRECT-first select 与办公目录登记。目录标签明确“单个公开入口”，警告说明全路径、跨国际站跳转及混合出口。涉及 `ruleset/Feishu.yaml`、`local-rulesets.json`、`catalog/services.json`、策略组与有序配置；不改旧服务。
2. 唯一活动引用放在基线全部 21 个 App 之后，即 Youku 之后、SiriAI 之前；保留安全/游戏及全部旧 App 优先，以及 SiriAI/Apple、五媒体、GlobalMedia、GeoIP/ChinaMax 后继顺序、Gemini 在 Google 前、所有旧规则相对顺序和 MATCH。
3. 新增 `validate_feishu(root)` 及真实 tree 一次 hook，复用已有 `app_policy` 与 `public_rules`，不改共享组件、payload 扫描或旧函数。固定范围/重复/引用/锚点/严格 select、DIRECT/手动代理/Final、UTF-8、manifest 冲突与缺失 provider、未知/不完整顶层规则、前置 IP/GeoIP fail-closed。
4. 新真实完整公共 fixture 先证明未变异 tree 可通过，再变异范围、引用、21 个前驱/全部后继、策略类型及复杂 keys/proxies、默认/可选出口、provider、IP、未知条件与空白字段。直接 helper 必须返回本 App 的明确诊断；tree 可由更早正确门禁拒绝，但必须匹配相同原因/规则类型，不能只接受任意异常或硬锁最后执行的 App 前缀。合法安全更新、合法 quoted/select 格式、负控与首匹配也须成功。
5. 既有离线 generator `--write` 重建 providers/目录/资产；专项、默认验证、生成一致性、diff 和完整测试均绑定精确候选内容。验证只使用公开临时 fixture 与离线模型，不替代实际客户端、DNS 或出口测试。

约束：不读取根目录私有配置/环境文件/订阅/节点，不请求真实登录、企业内容、下载或账号 API；不运行网络同步，不改来源锁、镜像、许可、工作流或权限，不安装新运行依赖。未来扩域须重新采证，依据不足时缩小或延期，不补猜测域名。当前范围固定为上述单个精确主机。

## English scope summary

The accepted scope is only `DOMAIN,www.feishu.cn`, provider `Feishu`, with a DIRECT-first `💼 飞书` group and optional manual proxy / Final. The domestic App Store developer metadata links directly to this host's privacy page and declares same-host terms/privacy URLs. Official download/help-page titles support the public-entry association, but readable page bodies, resource tags and installer destinations were not verified.

The homepage redirects to `www.larksuite.com/en_sg/` in the observed environment. The international target is excluded and retains its existing route; do not treat redirected Lark content as evidence for domestic Feishu endpoints. All paths on the one included host follow the group, while other requests keep their routes, allowing mixed egress. This is not complete native-app, tenant, login, document, chat, meeting, API, transfer or regional-eligibility coverage, and does not guarantee the domestic page remains selected. No account, tenant content, installer, private traffic or credentials were accessed. Verification uses fixed public candidates and disposable fixtures, not private inputs or live-client observations.
