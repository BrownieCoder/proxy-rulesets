# GitHub 服务目录审查记录

本轮按照用户要求，以 GitHub README、服务 Markdown 和公开规则文件作为唯一使用入口。此前的独立安装页、客户端选择与导入方案已撤销；旧方案留在 Git 历史，不作为当前验收依据。

## 目标与边界

首页找服务 → 服务页复制地址或查看规则。28 个服务均有入口；地址先于技术说明。保持原规则、策略、优先级、MATCH、来源、许可和权限不变。后续按用户授权推送 PR 分支并整合 main；尚未合并 PR 或部署。

## 独立技术审查

结论：PASS WITH FOLLOW-UPS，0 BLOCKER、0 MAJOR。已确认目录生成仍包含 provider 配置的一致性校验；同步候选树预检与失败保留旧文件的测试继续有效。唯一 MINOR（Claude 说明硬编码当前数量）已改为“上游基础清单”，实时条数只由生成器读取。

## 独立使用体验审查

结论：PASS，0 BLOCKER、0 MAJOR。28 个“获取地址”链接直接指向对应服务页的地址标题，ChatGPT 与 Siri 位于首组。抽查地址代码块均在页首，无须先理解策略。链接不会被描述为点击后自动复制。审查是本地文档与锚点核验，不是已经在线发布的声明。

## 验证

- `python3 scripts/validate.py`：通过，24 个镜像与 4 个本地规则集，生成目录/provider 一致。
- `python3 scripts/public_check.py`：通过。
- `python3 -m unittest discover -s tests`：25 项通过，含目录/地址/锚点、独立 YAML 解析、失败关闭和模拟同步成功/失败路径。
- `git diff --check`：通过。
- 原规则、canonical、config、来源清单与锁、LICENSE、THIRD_PARTY_NOTICES 与已整合的 main `5da48b5` 一致。
- 工作流权限无变化；删去废弃的网页测试，继续运行 Python 校验。
- 28 个公开规则 URL 已重新 GET；记录同时保存响应散列和检查时的本地快照散列，匹配结论仅属于 `checkedAt`，不代表之后的快照。具体结果见 `catalog/online-verification.json`。

## 后续事项

PR 分支已按授权推送。上一轮发现的额外 `--release` 检查白名单问题仍属基线问题：GitHub 自动合并提交使用的通用 noreply 邮箱不在旧白名单内；本次没有扩大范围修改扫描器。

权限变化：NONE。没有读取私人配置，没有执行生产网络同步。

## Copilot 后续校验修复

候选同步在替换文件前调用同一套 `validate_tree(root)`，包含来源散列、provider/策略组引用、规则顺序、目录与 Siri first-match 合同。新增测试证明上游 Privacy 抢先匹配 Siri 或策略组引用失效时，所有现有文件字节不变。测试依赖已固定版本、wheel 散列，并强制 hash 校验。
