# Security Policy / 安全说明

## English

This project contains routing data and update automation; it does not operate a proxy service or collect user traffic.

Report a security issue privately to the repository maintainer instead of opening a public issue when it involves:

- a compromised upstream or malicious ruleset update;
- workflow or supply-chain abuse;
- a rule that redirects sensitive traffic to an unsafe policy;
- accidentally committed credentials, private hostnames, or personal data.

Include the affected file, commit, impact, and a safe reproduction. Do not include live credentials or unredacted user traffic.

Ruleset correctness reports that do not expose sensitive information may use a normal issue.

The public policy-group template must never contain subscription URLs, proxy node
addresses, credentials, account identifiers, or private endpoints. Its automatic
groups perform health checks against `www.gstatic.com/generate_204`. Keep
international-game policies fail-closed; adding `DIRECT` can expose the user's
real network exit and defeat the international-service safeguard.

## 简体中文

本项目包含分流数据和更新自动化，不运营代理服务，也不收集用户流量。

以下问题请私下联系仓库维护者，不要直接创建公开 Issue：

- 上游被入侵或 ruleset 更新包含恶意内容；
- GitHub Actions 或供应链滥用；
- 规则把敏感流量导向了不安全策略；
- 仓库意外提交了凭证、私人主机名或个人数据。

报告应包含受影响文件、提交、影响和安全的复现方法。不要发送真实凭证或未脱敏用户流量。

不涉及敏感信息的普通规则准确性问题可以使用公开 Issue。

公开策略组模板中不得出现订阅 URL、代理节点地址、凭证、账号标识或私有端点。自动策略组会请求
`www.gstatic.com/generate_204` 进行健康检查。国际游戏策略应保持失败关闭；加入 `DIRECT`
可能暴露用户的真实网络出口，并使国际服保护失效。
