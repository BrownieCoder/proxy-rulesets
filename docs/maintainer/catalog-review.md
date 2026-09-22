# GitHub 服务目录审查记录

本轮按照用户要求，以 GitHub README、服务 Markdown 和公开规则文件作为唯一使用入口。此前的独立安装页、客户端选择与导入方案已撤销；旧方案留在 Git 历史，不作为当前验收依据。

## 目标与边界

首页找服务 → 服务页复制地址或查看规则。28 个服务均有入口；地址先于技术说明。保持原规则、策略、优先级、MATCH、来源、许可和权限不变。本轮不 push、merge 或 deploy。

## 独立技术审查

结论：PASS WITH FOLLOW-UPS，0 BLOCKER、0 MAJOR。已确认目录生成仍包含 provider 配置的一致性校验；同步候选树预检与失败保留旧文件的测试继续有效。唯一 MINOR（Claude 说明硬编码当前数量）已改为“上游基础清单”，实时条数只由生成器读取。

## 独立使用体验审查

结论：PASS，0 BLOCKER、0 MAJOR。28 个“获取地址”链接直接指向对应服务页的地址标题，ChatGPT 与 Siri 位于首组。抽查地址代码块均在页首，无须先理解策略。链接不会被描述为点击后自动复制。审查是本地文档与锚点核验，不是已经在线发布的声明。

## 验证

- `python3 scripts/validate.py`：通过，24 个镜像与 4 个本地规则集，生成目录/provider 一致。
- `python3 scripts/public_check.py`：通过。
- `python3 -m unittest discover -s tests`：20 项通过，含目录/地址/锚点、独立 YAML 解析、失败关闭和模拟同步成功/失败路径。
- `git diff --check`：通过。
- 原规则、canonical、config、来源清单与锁、LICENSE、THIRD_PARTY_NOTICES 相对公开基线 `322017d` 无变化。
- 工作流权限无变化；删去废弃的网页测试，继续运行 Python 校验。
- 28 个公开规则 URL 沿用前次成功 GET 的记录；时间未改，响应字节仍对应当前规则。历史在线证据不替代未来发布后的再次核验。

## 后续事项

本轮仅本地提交。上一轮发现的额外 `--release` 检查白名单问题仍属基线问题：GitHub 自动合并提交使用的通用 noreply 邮箱不在旧白名单内；本次没有扩大范围修改扫描器。

权限变化：NONE。没有读取私人配置，没有执行生产网络同步。
