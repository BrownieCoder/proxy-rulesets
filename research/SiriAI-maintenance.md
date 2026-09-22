# SiriAI 维护、证据与同步

核验日期：2026-09-22。唯一可编辑清单：[rules/siri-ai-domains.txt](../rules/siri-ai-domains.txt)，每行一个裸域名，全部精确匹配。来源逐条见 [provenance](../rules/siri-ai-provenance.json)。

## 证据分层

- **Apple 官方确认**：5 个正式主机用途来自[企业网络清单](https://support.apple.com/en-us/101555)。不代表官方要求使用某种代理或某国节点。
- **本项目验证**：离线格式、引用、SHA-256、当前公开 provider 域名规则首条命中及非目标回归模拟。
- **社区经验**：用户提供的三张社区截图，未提供原帖 URL/转载许可；仅作为候选线索，未转载图片或作者标识。
- **尚待验证**：具体设备上的完整功能、DNS/SNI 可见性、TCP/UDP 转发、出口地区、服务端状态；没有实机抓包或可用性结论。

18 条候选中 5 条接纳，5 条待验证，8 条拒绝作为默认规则，重复 0。原有 12 条后缀和 1 条关键词均不直接保留；接纳项中 4 条收窄为 DOMAIN。最明显的过宽项是 siri 关键词与 ls.apple.com 根域；smoot、gateway、mask、mzstatic 等还具有跨服务风险。拒绝不表示域名无效。新增域名目前为 0；后续候选须先补来源与复现证据，不能直接生成上线。

## 路由语义

原 Apple 的 apple.com 后缀会抢先命中 guzzoni 与 apple-relay.apple.com；插入 SiriAI 后由 🤖 AI 服务处理。其余 3 个 PCC 域名也在更宽 provider 前处理。Privacy/Hijacking 仍可以优先拒绝，国际游戏、国内游戏顺序不变。现有 group、其他规则相对顺序和 MATCH 均未改动。

DOMAIN 只匹配该主机，不匹配其子域，更不匹配整个 CDN。一般 Siri/听写与 AI 共用 guzzoni，因此不能宣称“其他所有 Apple 功能完全不受影响”；准确边界是只改变这五个精确主机。

[当前 Mihomo 规则说明](https://wiki.metacubex.one/config/rules/)指出：UDP 请求遇到不支持 UDP 的节点会继续向下匹配。离线域名模拟不判断 DNS、GeoIP、进程或节点 UDP 能力。启用前需在自己的客户端按 TCP/UDP 分别检查实际选组、节点及出口，不要用规则存在代替功能验证。

## 生成与验证

```sh
python3 scripts/siri_ai.py --write
python3 scripts/sync.py --generate-only
python3 scripts/validate.py
python3 scripts/public_check.py
python3 -m unittest discover -s tests -p 'test_siri_ai.py'
git diff --check
```

两个生成命令均离线。不要手改 ruleset/SiriAI.yaml 或两个 provider 配置，也不要为本服务更新无关镜像和 sources.lock.json。常规 validate.py 已包含 SiriAI 漂移与路由检查。同步 CI 权限没有改动。

## 与 SiriAI-RouteKit 的关系

选择 Option B：本仓库为 canonical，SiriAI-RouteKit 为中文教程与客户端生成镜像，不是第二个可编辑清单。维护者修改本仓库 canonical、provenance、审计并完成验证、review、本地 commit 后，在 SiriAI-RouteKit 中按其维护文档运行显式本地导入和 --source 跨库验证。导入应记录源仓库公开 URL、完整 commit 和三份文件 hash；不依赖私人根目录材料。

锁定提交保证可重复，不表示镜像总是追随源仓库最新提交。每次规则变化必须同步两仓库；跨库验证发现新的 canonical 后应失败并要求重新导入，不能静默升级。新仓库与本分支均未在本任务中推送或发布，所有远程入口须发布后再检验。

## 许可

新增代码、文档和规则采用 GPL-2.0-only，沿用 [LICENSE](../LICENSE)。Apple 文档只用作事实引用，其文档、商标仍归 Apple；社区截图亦未重新许可。自编规则依官方公开主机事实重新编制，没有复制未知许可证的社区规则文件或现有第三方镜像到新项目。
