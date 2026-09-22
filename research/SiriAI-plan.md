# Siri AI 接入研究与实施计划

核验日期：2026-09-22。状态：APPROVED FOR IMPLEMENTATION；本文件先于生产规则修改形成。

## 现有架构与基线

源仓库 `main` 基线 `acc447c30fff787d17af641a845ff02e0b205840`，与 `origin/main` ahead/behind 均为 0；只有本地未跟踪 AGENTS.md。已独立建立 `agent/siri-ai-rules` worktree。根工作区不是 Git 仓库，未读取任何私人配置。

24 个镜像由 sources.json + sources.lock.json 管理；3 个自维护 provider 由 local-rulesets.json 管理。sync.py 负责镜像和 provider 生成；--generate-only 已有离线生成入口。validate.py 检查校验和、引用、策略组循环、游戏与 Gemini 顺序；public_check.py 检查公开材料。现有 CI 每日同步且有 contents: write，本任务保持其权限和同步范围原样。

基线命令 scripts/validate.py、scripts/public_check.py、git diff --check 均通过。

## 当前 Apple / AI 路由与冲突

顺序为 Privacy → Hijacking → 国际游戏精确例外 → InternationalGaming → ChinaGaming → Apple → 其他服务/AI → GlobalMedia → GEOIP CN → ChinaMax → Lan → MATCH。
Apple provider 包含 apple.com 后缀，目标 🍎 Apple 首选 DIRECT。OpenAI/Gemini/Claude 在 Apple 后。若新增 Siri 放在已有 AI 行附近，guzzoni.apple.com 和 apple-relay.apple.com 会提前进入 Apple。新的 SiriAI 放在 ChinaGaming 之后、Apple 之前是必要的一行插入；不重新排列任何既有规则。安全规则仍优先。

## 方案比较

| 方案 | 判断 |
| --- | --- |
| 混入现有 AI provider | 不利于独立审计与多客户端复用，REJECT |
| 并入 Apple 策略 | 默认 DIRECT，不表达本任务出口选择，REJECT |
| Global / Proxy | 缺乏 AI 配置入口，DEFER |
| 独立 SiriAI provider + 🤖 AI 服务 | 最小改动，APPROVE FOR IMPLEMENTATION |
| 新建 Siri AI 策略组 | 当前没有必须独立选区的额外合同，DEFER |

🤖 AI 服务仍提供 DIRECT；必须由用户在客户端选好实际出口。官方主机用途不等于官方要求代理，也不能保证任一地区节点解锁资格。

## 用户规则审计

截图共 18 条唯一候选，0 重复；5 条 DOMAIN、12 条 DOMAIN-SUFFIX、1 条 DOMAIN-KEYWORD。只采纳官方确认的 guzzoni.apple.com、apple-relay.apple.com、apple-relay.cloudflare.com、apple-relay.fastly-edge.com、cp4.cloudflare.com；全部使用 DOMAIN，后四条收窄匹配范围。

依据：[Apple 企业网络主机清单](https://support.apple.com/en-us/101555)。guzzoni 同时承载普通 Siri/听写；其他四项为 PCC 或 Apple Intelligence 扩展。接受这项已披露影响，不声称五条只涵盖 Siri AI。其他规则的逐条结论见后续 SiriAI-audit.json；共享搜索、Private Relay、CloudKit、内容分发和关键词不进入默认集。没有额外新域名获得生产批准。

## Apple 官方资格核验

以 [新一代 Apple 智能](https://support.apple.com/zh-cn/121115) 与 [Siri AI Beta](https://support.apple.com/zh-cn/148218) 分开记录。当前页面涉及 27 系列系统；Siri AI Beta 的设备及 Siri 语言须为英语，不能据 Apple 智能支持中文推断其支持中文。中国大陆销售设备限制、人在大陆且账号地区为大陆的限制仍须按官方文字判断。旧系统的既有 Apple 智能功能与新一代功能不混用最低版本。详细条件与存储分类将在新仓库教程中列出。

## 唯一来源与许可证

选择 Option B：proxy-rulesets 的 rules/siri-ai-domains.txt 为唯一可编辑清单；rules/siri-ai-provenance.json 记录证据。生成 ruleset/SiriAI.yaml。SiriAI-RouteKit 从明确的本地公开源仓库提交导入这两份文件，记录完整提交号和 SHA-256，生成两种客户端规则与示例。新仓库镜像不可独立增删域名。锁定版本保证可重复；更新源后需显式重新导入，跨库校验必须报出未同步，不能把离线锁校验称为最新源检查。

两边自编材料采用 GPL-2.0-only，保留 GNU 原文许可证。新仓库不复制既有第三方镜像或截图图像/文案；截图仅作为候选来源身份记录，生产域名用途独立依据 Apple 官方主机事实重新编制。未获授权的社区配置不转载。参考 [GNU GPL v2 正文](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)。中文文档要求不适用于应原样保留的英文法律正文与协议字段。

## 最小实施计划

目标：可追溯的窄域分流、不会被 Apple 抢先匹配、两库同源、中文入门与排障完整。
约束：安全及游戏顺序、无关 Apple 流量、现有 FINAL、镜像文件与锁、私人配置、权限均保持不变。
不做：MITM、CA、真实订阅/节点、全 Apple 代理、远端同步、发布或推送。

| 工作 | 改动及收益 | 风险/依赖 | 验证 | 决策 |
| --- | --- | --- | --- | --- |
| 审计/官方事实 | 逐条来源与资格核验；避免错用教程 | 动态官方条件 | URL、核验日、分层标记 | APPROVE FOR IMPLEMENTATION |
| canonical/生成器 | 5 个精确域；单一维护位置 | 依赖官方用途证据和独立方案 review | 去重、语法、空集、hash、漂移 | APPROVE FOR IMPLEMENTATION |
| existing 接入 | local manifest、provider生成、一行路由 | 普通 Siri/听写也随目标组 | first-match、非目标回归、现有默认检查 | APPROVE FOR IMPLEMENTATION |
| 新独立仓库 | 双格式、无节点示例、中文文档、轻量校验 | 与源提交锁一致；可与 existing 实现并行 | 导入锁、生成一致、引用、CLI语法（若可用） | APPROVE FOR IMPLEMENTATION |
| 客户端实机复现 | 流量命中、TCP/UDP、实际地区 | 无真实设备/节点证据 | 脱敏现场测试 | MEASURE FIRST |
| 共享/broad 域 | 不进入生产；保留研究理由 | 无专用链路证据 | 以后获得脱敏可复現观察再评审 | DEFER / REJECT |
| 发布 | 本次仅本地 commit | 用户未授权远端公开 | 发布前检查远端文件和链接 | DEFER |

独立 review 通过后按任务正文第 25 节已有授权实施；若需要扩大 Apple 路由、权限或访问私人数据，停止该部分并升级。验收须包括两个仓库的引用/一致性校验、独立实现 review、无未批准权限变化；未运行实机测试必须在交付中明示。

## 独立方案评审

2026-09-22 独立 reviewer：PASS，0 Blocker / Major。已独立检查五个目标不被当前安全/游戏 DOMAIN、SUFFIX、KEYWORD 提前匹配；确认 Apple 的 apple.com 后缀冲突。实施要求：真实提交导入与双 hash、离线模拟如实标注、非目标样本回归、未发布时本地导入可操作、保持现有 workflow。PCC 的 TCP/UDP 能力与实际客户端命中需现场验证；Mihomo 文档说明不支持 UDP 的节点可能令 UDP 请求继续向后匹配。
