# Claude 与 Datadog 共享域的路由边界

核实日期：2026-11-17。基线 `3ee79fedd218dc178efd91251d7fbf48ca2b8b17`。

## 证据与已接受修复

- [Datadog 官方网络文档](https://docs.datadoghq.com/agent/configuration/network/)说明 Agent 的监控、日志、API 等通用平台通信，并列出多个 Datadog 站点；不能把 `datadoghq.com` 整根视为 Claude 专属服务。
- [Claude 官方企业网络文档](https://code.claude.com/docs/en/network-config)确实列出 `http-intake.logs.us5.datadoghq.com` 与 `browser-intake-us5-datadoghq.com` 两个可选遥测入口。它证明使用关系，不证明共享服务主机独占，也不支持整个 Datadog 根域绑定 Claude。
- 已接受的最小修改仅删除有序模板的 `DOMAIN-SUFFIX,datadoghq.com,🧠 Claude`，不猜测或增加任何 exact 替代。其他 Claude 补充、上游镜像和策略组不变；目录补充计数由 10 改为 9，由离线生成器更新派生文档。

## 实际影响与证据边界

读取公共 manifests、规则文件及真实活动顺序，使用现有域名模型模拟：

| 公开主机 | 修改前首匹配 | 删除该行后 |
| --- | --- | --- |
| `app.datadoghq.com` | Datadog 根后缀 → Claude | MATCH → Final |
| `api.datadoghq.com` | Datadog 根后缀 → Claude | MATCH → Final |
| `agent-http-intake.logs.datadoghq.com` | Datadog 根后缀 → Claude | MATCH → Final |
| `http-intake.logs.us5.datadoghq.com` | Datadog 根后缀 → Claude | MATCH → Final |
| `browser-intake-us5-datadoghq.com` | MATCH → Final | 不变（原本就不是上述根域的子域） |

Final 是用户已有的通用出口策略，不等于固定直连或固定代理。移除绑定不是禁止或阻断 Claude 遥测；受该后缀影响的可选遥测也会回到一般路由，出口可能变化。未实测真实客户端、遥测送达、DNS、GeoIP 或代理连通性，不保证功能或可用性。

回归读取实际有序配置与公共 provider，覆盖三个通用 Datadog 主机不再归 Claude、九条原有补充及核心 Claude 主机保持、非 Datadog 边界不变、Privacy / Hijacking 优先，并通过内存回插旧后缀证明误绑定。安全注入仅在内存模型完成，不改镜像、来源锁或真实配置。

## English scope summary

Remove only the shared `datadoghq.com` suffix override from the Claude policy. Datadog documents general platform traffic, while Claude documents two optional telemetry hosts; usage does not establish exclusivity. No replacement host is added. Affected traffic falls back to the existing general routing policy, not a new block or a guaranteed DIRECT route. Other Claude rules, security priority, mirrored sources, permissions and workflows remain unchanged. Verification is offline domain first-match simulation, not live client or telemetry testing.
