# Third-party notices / 第三方声明

## English

This repository contains two kinds of material:

1. Project-authored code, documentation, and local rules listed in `local-rulesets.json`.
2. Mirrored ruleset snapshots listed in `sources.json`.

The mirrored rules are sourced from [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script), whose repository identifies GNU GPL v2.0 and also publishes additional usage and disclaimer statements in its README. Preserve upstream headers and attribution, review the current upstream terms before redistribution, and do not imply that upstream authors endorse this repository.

Each mirrored file retains its upstream header where provided. `sources.lock.json` records the source URL, final URL, size, upstream SHA-256, normalized SHA-256, and synchronization time.

Game names, company names, service names, and trademarks belong to their respective owners. Their appearance is solely for interoperable routing identification and does not imply affiliation or endorsement.

## 简体中文

本仓库包含两类内容：

1. 项目自行编写的代码、文档，以及 `local-rulesets.json` 中列出的本地规则。
2. `sources.json` 中列出的镜像 ruleset 快照。

镜像规则来自 [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script)。该仓库标明 GNU GPL v2.0，同时在 README 中发布了额外的使用和免责声明。再分发前应保留上游文件头和署名，并复核上游最新条款；不得暗示上游作者为本仓库背书。

在上游提供文件头的情况下，本仓库会原样保留。`sources.lock.json` 记录来源 URL、最终 URL、文件大小、上游 SHA-256、规范化后 SHA-256 和同步时间。

游戏、公司、服务名称及商标归各自权利人所有。本仓库仅为兼容分流而进行识别，不代表任何隶属或背书关系。

## SiriAI 来源

新增 SiriAI 为依 Apple 官方公开主机事实重新编制的精确规则，逐条证据在 rules/siri-ai-provenance.json。用户提供的社区截图仅作为研究线索，未转载图像、署名标识或整份社区配置。Apple 官方资料仅引用链接，不将其正文重新许可为 GPL；相关商标与文档权利仍属 Apple。

## Generated install formats / 生成安装格式

`modules/privacy.module` is mechanically derived from the existing Privacy snapshot without changing its ordered match rules. It retains upstream header comments and source/hash references. The upstream ownership, GPL-2.0 identification and additional usage/disclaimer statements above also apply to derived formats; generation does not establish new ownership or endorsement.

`modules/privacy.module` 从现有 Privacy 快照机械生成，保留匹配规则的顺序、上游文件头、来源与散列。上述上游归属、GPL-2.0 标识及额外使用/免责声明同样适用于衍生格式；转换格式不改变版权归属，也不代表背书。
