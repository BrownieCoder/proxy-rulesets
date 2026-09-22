# 高级 / 手动配置

[返回安装目录](../README.md)

这些文件是片段，不是完整配置。只在自己的本地配置中接入节点，不要提交任何私人配置。

1. 使用已有节点或自己的 provider。
2. 合并[策略组](../config/proxy-groups.yaml)。已有同名组时先核对，不能盲目覆盖。
3. 合并[远程规则集合](../config/rule-providers.remote.yaml)，或本地使用[本地集合](../config/rule-providers.local.yaml)。
4. 按[有序规则模板](../config/rules.yaml)接入引用。不要改变最后一条 MATCH 的目标；也不要直接覆盖自己的完整规则数组。
5. 如不采用本项目策略组，将目标映射到自己已有的真实策略组，保留直连、拒绝和可选出口的区别。
6. 使用客户端检查或 `mihomo -t -f your-config.yaml` 后检查实际连接。

顺序：Privacy 拒绝 → Hijacking 可选防护 → 游戏精确例外 → 国际游戏 → 中国游戏 → Siri AI → Apple → 其他服务 → 国际媒体 → GEOIP CN → ChinaMax → LAN → MATCH。

国际游戏只提供代理出口；中国游戏固定直连。SteamCN 包含全球共享后缀，仍走 Steam 可选策略。Gemini 必须先于 Google。Siri AI 使用现有 AI 可选策略，而不是强制某地区；网络规则不改变 Apple 资格。

自动选择和美国节点组使用公开健康检查地址，空组按原配置失败关闭为 REJECT。节点是否支持 UDP 会影响实际行为。

[中国游戏审计](../research/ChinaGaming-audit.md) · [Siri AI 审计](../research/SiriAI-audit.json) · [Siri AI 维护](../research/SiriAI-maintenance.md)
