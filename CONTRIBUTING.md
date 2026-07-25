# Contributing / 贡献指南

## English

Thank you for helping improve the rules.

### Before opening a pull request

1. Search existing rules and ChinaMax first.
2. Identify whether the endpoint is mainland-only, international-only, or shared.
3. Prefer the narrowest stable rule:
   - exact `DOMAIN` for shared root domains;
   - `DOMAIN-SUFFIX` only when the entire root has a consistent routing boundary;
   - never add a broad cloud/CDN root based on one observed customer hostname.
4. Include authoritative evidence, preferably an official website, client document, API document, installer manifest, or reproducible runtime log.
5. Explain the international-service false-positive risk.
6. Do not submit credentials, account identifiers, signed download URLs, private hostnames, or unredacted packet captures.

### Evidence template

```text
Game/company:
Proposed rule:
Desired policy: DIRECT / proxy
Mainland or international:
Official evidence URL:
Observed client flow: startup / login / update / match
Already covered by:
Shared-root risk:
Notes:
```

### Validation

```bash
python3 scripts/validate.py
git diff --check
```

If a mirrored source changes, run `python3 scripts/sync.py` first. Do not manually edit files managed by `sources.json`.

## 简体中文

感谢你帮助改进规则。

### 提交 Pull Request 前

1. 先检索现有规则和 ChinaMax。
2. 判断端点属于中国大陆、国际服，还是中外共享。
3. 优先选择最窄且稳定的规则：
   - 根域中外共享时使用精确 `DOMAIN`；
   - 只有整根域名边界一致时才使用 `DOMAIN-SUFFIX`；
   - 不要因为观察到一个客户子域，就加入整个云厂商/CDN 根域。
4. 附上权威证据，优先官方页面、客户端文档、API 文档、安装清单或可复现运行日志。
5. 说明误伤国际服务的风险。
6. 不要提交凭证、账号标识、带签名下载链接、私人主机名或未脱敏抓包。

### 证据模板

```text
游戏/公司：
建议规则：
目标策略：DIRECT / 代理
中国大陆或国际服：
官方证据 URL：
观察链路：启动 / 登录 / 更新 / 对局
当前已被什么规则覆盖：
共享根域风险：
备注：
```

### 校验

```bash
python3 scripts/validate.py
git diff --check
```

镜像来源变化时先运行 `python3 scripts/sync.py`。不要手动修改由 `sources.json` 管理的文件。
