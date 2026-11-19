# Payload YAML 原始字符检查

公开 `ruleset/*.yaml` 在提取条目、分行或忽略注释之前，先检查完整 UTF-8 文本。注释中的原始 VT、FF 等非法字符也必须被拒绝，不能因为 Python 的 `splitlines()` 将其吞掉而通过验证。

检查遵循 [YAML 1.2.2 §5.1 的 c-printable 字符范围](https://yaml.org/spec/1.2.2/#51-character-set)：拒绝非法 C0/C1、DEL、代理码点及 U+FFFE/U+FFFF；允许 TAB、LF、CR、NEL，以及该范围内的中文、emoji、U+2028/U+2029 和格式字符。字符合法不代表它在任意 YAML 位置都合法，后续仍保留各入口既有的受限语法验证。

`scripts/yaml_characters.py` 使用标准库预编译正则，供目录生成、离线域名模型的 payload 读取及同步 payload 验证共用。它只检查原始字符，不删除、不替换、不规范化内容；错误仅报告码点与从 1 开始的字符位置，不回显原文。

此检查不改变 `config/rules.yaml` 的结构解析，也不应用于非 YAML 的 canonical 文本或 Surge 源文本。没有新增运行时依赖、域名、路由或权限。

维护时可离线运行：

```bash
python3 -m unittest discover -s tests -p 'test_payload_yaml_characters.py'
python3 scripts/validate.py
python3 scripts/public_check.py
git diff --check
```

回归使用公开临时 fixture，覆盖非法原始字符、合法 Unicode/LF/CRLF、三个读取入口、完整树验证及生成失败时无资产写入。同步用例只模拟公开下载响应，不发起网络同步；PyYAML 仅作为已有测试环境中的独立 oracle，不是新增运行时依赖。
