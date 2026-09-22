# 安装体验改造方案与边界

核验日期：2026-09-22。基线：公开 main，322017d；24 个镜像与 4 个本地规则集。

## Goal

首页先选服务和客户端，再提供可验证的一键、复制地址与最短手动路径。

## Constraints / Non-goals

不修改规则、域名分类、原策略组、有序路由、MATCH、来源、许可证及任何权限；不生成节点或订阅，不启用 Pages，不 push/merge/deploy。保留已有 Siri canonical 生成链。

## Acceptance criteria

28 个服务均可找到；所有目录来自真实清单；模块与来源按顺序完全相等；生成资产和散列无漂移；已有路由检查及公开安全检查通过；页面按钮不把规则误当订阅；有三步 fallback；未经上线核验不宣传线上可用。

## Tasks / Decision

| 问题 | 最小修改与收益 | 风险、依赖与验证 | 决策 |
| --- | --- | --- | --- |
| 工程目录难检索 | catalog/services.json + 生成目录和服务页 | 引用真实清单、按原策略解释；逐服务校验 | APPROVE FOR IMPLEMENTATION |
| 可选策略不能扁平化 | 仅 Privacy 固定 REJECT 生成 module；其他手动 | module 类型、规则序列、no-resolve、来源、hash；模块高于主配置 | REDUCE SCOPE |
| 客户端能力易误导 | 记录当前源码/文档证据，区别完整配置与规则 | 不向 profile scheme 传 provider URL | APPROVE FOR IMPLEMENTATION |
| 安装操作不明确 | 原生静态页，选服务、选客户端、复制、三步回退 | 无框架/外部资源；可并行在独立 worktree 实施 | APPROVE FOR IMPLEMENTATION |
| 生成内容可能漂移 | 复用现有 provider generator，离线生成及验证、轻量负向测试 | 同步 CI 加生成/暂存文件，不改权限；不执行同步 | APPROVE FOR IMPLEMENTATION |
| Pages 未启用、新资产未发布 | 准备文件、核验 raw 链接，明确未发布 | Settings/API 只读确认 has_pages=false；上线另行决定 | HUMAN DECISION REQUIRED |

用户任务已明确授权以上本地改造与本地提交，无需重复审批；发布和权限改变未获授权。

## Independent plan review

独立只读 reviewer 确认应收缩模块范围：AI 等 select group 允许 DIRECT、节点/地区选择，固定 PROXY 不等价。模块优先主配置会使 featuregates.org、segment.io（OpenAI）与 statsig.anthropic.com（Claude）绕过 Privacy；国际游戏还依赖 fastcdn.hoyoverse.com 的精确 DIRECT 例外。ChinaGaming 和 LAN 独立 DIRECT 也不安全。

Claude provider 仅含 3 条，主路由还有 10 条补充；目录必须说明复制 provider 不等于完整 Claude 配置。Privacy 是主路由第一项、固定 REJECT，只有 DOMAIN、DOMAIN-SUFFIX、DOMAIN-KEYWORD、IP-CIDR，可保持规则条目与目标；不承诺与用户任意已有配置完全等效。
