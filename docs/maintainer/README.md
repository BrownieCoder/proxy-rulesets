# 维护指南

[GitHub 服务目录](../../README.md#服务目录)

## 来源与生成

`sources.json` 定义镜像来源；`sources.lock.json` 保存上游 URL 与原始字节散列。镜像快照位于 `ruleset/`，不得手改。本地规则登记在 `local-rulesets.json`；Siri AI 继续从 `rules/siri-ai-domains.txt` 经现有 `scripts/siri_ai.py` 生成。

`catalog/services.json` 只维护公开服务名称、分类和说明。实际目标从 `config/rules.yaml` 读取，不另造策略。`scripts/generate_catalog.py` 输出 README 目录、29 份 Markdown 服务页、`catalog/index.json`、`catalog/assets.lock.json`，并保留原 provider 配置的生成和一致性校验。

## 离线检查

```bash
python3 scripts/generate_catalog.py --write
python3 scripts/validate.py
python3 scripts/public_check.py
python3 -m unittest discover -s tests
git diff --check
```

测试依赖固定为 PyYAML 6.0.2，并在 `requirements-dev.txt` 记录 PyPI wheel 的 SHA-256；使用 `python3 -m pip install --require-hashes -r requirements-dev.txt` 安装，依赖升级时须重新审查版本和散列。生成器仅使用 Python 标准库。上述生成和验证不下载上游、不访问私人配置。

### 有序规则模板的受限 YAML 语法

`config/rules.yaml` 由标准库模块 `scripts/public_rules.py` 统一读取；校验、目标与 provider 引用、服务目录、各 App 和 Siri 首匹配不再分别扫描所有列表行。此接口只用于本仓库公开模板，不是通用 YAML 或私人配置解析器；ruleset 的 `payload` 读取合同不变。

- 唯一顶层键必须是字面量 `rules:`，值为非空的 block 字符串列表。允许空行、整行注释、LF/CRLF，以及一致的空格缩进；不接受额外键、重复键（包括引号等价键）、嵌套层级、流式列表或非字符串项。
- 列表项支持现有大写规则类型开头的单行字面量，以及整条单/双引号包裹的无转义字符串。裸值不允许会改变 YAML 含义的 `: `、行内 `#`、引号、反斜杠或 flow 符号；若这些字符位于已支持的引号内则按字面值保留。引号内不支持同类引号转义/重复或反斜杠转义。语义错误仍由既有规则类型、字段、引用与顺序门禁拒绝。
- 锚点、别名、tag、merge、复杂键、多文档、block scalar、tab 和 Unicode 控制/格式字符一律 fail closed；合法但不在上述子集的 YAML 也会被拒绝。独立 PyYAML 只在测试中核对每个接受样例的实际字符串与顺序，不是运行时依赖。

English: the public ordered-rule template accepts one literal `rules` key with a nonempty, consistently indented block string sequence. Plain routing literals and unescaped whole quoted strings share one reader across validation, references, catalog and Siri/App routing. Complex YAML, duplicate/extra keys, ambiguous plain scalars and control characters are rejected. This is a deliberately restricted stdlib-only template contract, not a general YAML parser; rule content and first-match order remain unchanged.

只有明确需要同步时才运行 `python3 scripts/sync.py`。同步先在候选目录执行与 `validate.py` 相同的完整验证（来源散列、配置引用、路由顺序、Siri 合同及生成目录），再替换现有资产；校验失败时保留旧文件。候选目录也检查遗留服务页；服务改名后须先审查旧页的移除。规则解析只接受单行字面量和一致缩进，不接受 YAML 转义、嵌入引号或映射值，避免生成结果与 YAML 语义不同。GitHub Actions 沿用已有权限，并一同保存更新后的目录文件。

### 策略组模板的受限 YAML 语法

`config/proxy-groups.yaml` 由标准库模块 `scripts/public_policy_groups.py` 建立真实 mapping-list 模型。`parse_policy_groups` 的 `(names, members)` 接口保持不变，组名、成员引用及循环检查全部来自模型，不再扫描任意根键下的列表行。此接口只读取仓库公开模板，不是通用 YAML 或私人配置解析器。

- 仅允许一个 `proxy-groups` 顶层键（裸键或无转义单/双引号等价键），其值必须是非空 block mapping 列表；组、字段、成员分别使用 2/4/6 个空格缩进。错误、重复、额外根键、嵌套层级、流式集合及非 mapping 组项均拒绝。
- 字段限于当前模板的 13 种：`name`、`type`、`proxies`、`include-all`、`exclude-type`、`url`、`interval`、`timeout`、`tolerance`、`lazy`、`expected-status`、`empty-fallback`、`filter`。组名必须是非空字面字符串，所有字段键唯一，包含引号等价键。`proxies` 若出现必须为非空 block 字符串列表，不能用 null、标量或 flow 列表代替；仅字段缺失时模型成员为 `[]`，兼容现有两个动态 `url-test` 组。
- 字符串支持简单 ASCII 裸字面量、简单 HTTP(S) URL，或无转义的整条单/双引号字面量；空格及正则特殊符号应放在引号内。引号内的空格、`#`、URL 冒号及 filter 正则字符原样保留，不作 trim。仅引号外且有空格分隔的 `#` 为行内注释。裸 URL 不能以冒号结束，避免与 YAML 映射语法分叉。
- 布尔字段只接受裸 `true` / `false`，整数采用不带前导零的十进制字面量；不把带引号数字、布尔或 null 强制转换。锚点、别名、tag、merge、转义、block scalar、多文档、tab 和 Unicode 控制/格式字符均失败关闭。LF/CRLF、空行、注释及受限的引号键/`select` 形式有独立 PyYAML 语义对照。
- 此模型不代替 Mihomo 参数范围、动态节点或实际网络验证。现有 App 的 select/type/body、DIRECT-first 和出口选项门禁保留；结构非法可能由更早的共享入口抛出清晰 ValueError，不能为了保留旧报错前缀接受歧义结构。PyYAML 仅用于测试，运行时仍只依赖标准库。

English: one literal `proxy-groups` key (plain or unescaped quoted) owns a nonempty block list of group mappings. A strict 2/4/6-space, finite-field reader preserves real scalar types and ordered string members; missing `proxies` is distinct from explicit null/flow values. Quoted contents are never trimmed, and comments are recognized only outside quotes at a YAML separator. Duplicate keys, ambiguous values, complex YAML and hidden controls fail closed. References/cycles and existing App-specific policy semantics consume the model without changing routing data or introducing a runtime YAML dependency.

## 公开地址检查

```bash
python3 scripts/check_catalog_urls.py --record
```

只 GET 目录中的公开规则 URL，记录 HTTP 状态、响应散列和检查时的本地快照散列到 `catalog/online-verification.json`；匹配结论仅属于该次检查，不会同步规则。默认地址使用现有公开仓库的 main 分支，生成文档通过正常 Git 提交流程更新。

## 保持不变

原始规则、分流顺序、策略组、MATCH、来源和许可不由目录重构改变。任何规则变更继续遵循原有审计与验证要求。现有域名模拟不替代 DNS、GeoIP、UDP 或真实网络检查。
