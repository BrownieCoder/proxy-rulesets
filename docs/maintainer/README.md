# 维护指南

[用户安装入口](../../README.md) · [实施方案](install-plan.md) · [客户端证据](client-capabilities.md)

## 单一规则来源

`sources.json` 中的镜像以已锁定的 `ruleset/` 快照为本地转换输入；`sources.lock.json` 保留上游 URL 与散列。不要手改镜像。本地规则清单在 `local-rulesets.json`；Siri AI 从 `rules/siri-ai-domains.txt` 经现有 `scripts/siri_ai.py` 生成，安装生成器再次验证 canonical 一致性。

`catalog/services.json` 只保存公开服务文案和规则清单引用。实际策略从 `config/rules.yaml` 读取，不另写一套策略映射。客户端差异在 `catalog/clients.json`。Privacy 只有固定 REJECT 且位于原规则第一条时才生成 module；新的类型或策略会拒绝生成，不能静默裁掉不兼容规则。

## 离线生成与验证

```bash
python3 scripts/generate_install_assets.py --write
python3 scripts/validate.py
python3 scripts/public_check.py
python3 -m unittest discover -s tests
node --test tests/install_ui.test.cjs
git diff --check
```

生成：原 provider 配置、Privacy module、28 个服务页、README 的标记区域、安装目录 JSON/JS、可离线阅读的 HTML 教程、资产散列清单。所有规则都保留原始有序序列和 no-resolve。未生成的模块有具体原因。

YAML 解析测试依赖 `requirements-dev.txt`，运行测试前按清单安装测试依赖；生产离线生成只用 Python 标准库。生成和检查不会下载上游，不会访问私人配置。

仅在明确需要同步时执行 `python3 scripts/sync.py`。既有同步流程更新快照后会重新生成安装资产；CI 沿用现有权限，不新增 Pages/deployment 权限。每次同步仍须审查完整 diff、来源和许可。

## 上线门槛

本任务仅本地提交。GitHub Pages 在 2026-09-22 查询为未启用；不擅自更改设置。静态页可从仓库根目录提供服务，访问 `/install/`，或直接打开 `install/index.html`。没有第三方脚本、字体、分析或登录。

`catalog/publication.json` 初始 `siteUrl=null`、模块未发布。只有授权发布之后，才能运行在线 GET 检查，并据实际结果启用发布标记：

```bash
python3 scripts/check_install_urls.py --record
```

检查记录保存到 `catalog/online-verification.json`，包含状态与响应散列。模块首次发布前应核对记录散列与本地生成模块一致，发布标记要求已有成功 GET 记录；后续同步以本地一致性检查为准，更新后的远端散列须在发布后再核验；站点标记要求成功 GET。发布前的 404 是未完成上线门槛，不能宣称线上 READY。不要为了通过检查提前启用标记。

启用 Pages 需要人类决定设置；在此之前首页不链接一个虚构的可用安装站。若以后获准采用 Pages，其入口为项目站根下 `/install/`，并检查相对资源、文档路径和手机浏览器唤起。README 的发布说明也须按真实状态更新。

## 不变合同

所有原始规则、策略组、规则顺序、MATCH、licenses、provenance 保持原样。现有 Siri AI 离线模拟覆盖安全、游戏与 3136 个非目标样本，但它不是设备、DNS、UDP 或 GeoIP 的真实测试。

## 可选浏览器回归

安装 Playwright 后运行 `node tests/browser_install.cjs`；使用系统 Chrome 时通过 `BROWSER_EXECUTABLE_PATH` 指定可执行文件。脚本只打开本地文件，验证服务选择、未发布按钮门槛、复制失败回退、HTML 教程和六个宽度；不会触发外部客户端 scheme。截图保存在系统临时目录。CI 中的 Node 测试只检查目录与入口合同，不代替浏览器或真机测试。
