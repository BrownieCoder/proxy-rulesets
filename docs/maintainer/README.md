# 维护指南

[GitHub 服务目录](../../README.md#服务目录)

## 来源与生成

`sources.json` 定义镜像来源；`sources.lock.json` 保存上游 URL 与原始字节散列。镜像快照位于 `ruleset/`，不得手改。本地规则登记在 `local-rulesets.json`；Siri AI 继续从 `rules/siri-ai-domains.txt` 经现有 `scripts/siri_ai.py` 生成。

`catalog/services.json` 只维护公开服务名称、分类和说明。实际目标从 `config/rules.yaml` 读取，不另造策略。`scripts/generate_catalog.py` 输出 README 目录、28 份 Markdown 服务页、`catalog/index.json`、`catalog/assets.lock.json`，并保留原 provider 配置的生成和一致性校验。

## 离线检查

```bash
python3 scripts/generate_catalog.py --write
python3 scripts/validate.py
python3 scripts/public_check.py
python3 -m unittest discover -s tests
git diff --check
```

测试依赖见 `requirements-dev.txt`；生成器仅使用 Python 标准库。上述生成和验证不下载上游、不访问私人配置。

只有明确需要同步时才运行 `python3 scripts/sync.py`。同步先在候选目录完成全部格式和目录验证，再替换现有资产；校验失败时保留旧文件。GitHub Actions 沿用已有权限，并一同保存更新后的目录文件。

## 公开地址检查

```bash
python3 scripts/check_catalog_urls.py --record
```

只 GET 目录中的公开规则 URL，记录 HTTP 状态与响应散列到 `catalog/online-verification.json`；不会同步规则。默认地址使用现有公开仓库的 main 分支，生成文档通过正常 Git 提交流程更新。

## 保持不变

原始规则、分流顺序、策略组、MATCH、来源和许可不由目录重构改变。任何规则变更继续遵循原有审计与验证要求。现有域名模拟不替代 DNS、GeoIP、UDP 或真实网络检查。
