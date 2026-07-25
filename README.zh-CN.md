# Proxy Rulesets

[English](README.md) | [简体中文](README.zh-CN.md)

这是一个自维护的 Clash/Mihomo ruleset 镜像，并包含经过证据审计的中国大陆游戏分流层。

仓库直接保存并校验规则快照，不只依赖第三方 URL。同时，它把中国大陆游戏服务和国际服拆开：大陆流量优先走 `DIRECT`，国际游戏流量继续交给美国节点或其他代理策略。

## 主要特性

- 24 份带 SHA-256 锁定的上游镜像
- 3 份自维护规则，包括 `ChinaGaming` 与 `InternationalGaming`
- 93 条高优先级中国大陆游戏规则
- 25 条国际游戏保护规则
- 原子同步：只有全部下载并校验成功后才替换现有快照
- GitHub Actions 每日自动检查更新
- 离线检查文件、校验和、provider 引用、重复规则和规则优先级
- 审计覆盖腾讯/WeGame/三角洲行动、网易、米哈游、完美世界、西山居、莉莉丝、朝夕光年、库洛、鹰角、叠纸、Bilibili 游戏、TapTap、4399 等

## 分流模型

```text
安全与拒绝规则
        ↓
已确认的国际游戏 → 最终代理 / 美国节点
        ↓
中国大陆游戏     → DIRECT
        ↓
其他服务规则
        ↓
已确认的国际媒体
        ↓
GEOIP CN          → DIRECT
        ↓
ChinaMax / LAN / Final
```

Mihomo 采用从上到下首条匹配，因此顺序本身就是设计的一部分。`InternationalGaming` 必须位于 `ChinaGaming` 之前，两者都应位于 Bilibili、Steam、GlobalMedia、ChinaMax 等宽泛 provider 之前。

`fastcdn.hoyoverse.com` 是一个有意保留的精确例外：它被米哈游国服页面使用，所以先设为 `DIRECT`，再匹配 HoYoverse 国际服后缀。

## 快速开始

仓库发布后使用远程 provider 模板：

1. 将 [`config/rule-providers.remote.yaml`](config/rule-providers.remote.yaml) 中的 `rule-providers` 合并进 Mihomo 配置。
2. 按顺序合并 [`config/rules.yaml`](config/rules.yaml)。
3. 将 `🧭 Final`、`🕹️ Steam`、`🇨🇳 China-Global` 等策略名替换为你配置中真实存在的策略组。
4. 启用前运行 `mihomo -t -f your-config.yaml`。

如果配置和仓库位于同一目录，可使用 [`config/rule-providers.local.yaml`](config/rule-providers.local.yaml)。

## 中国大陆游戏保护

[`ruleset/ChinaGaming.yaml`](ruleset/ChinaGaming.yaml) 优先匹配中国大陆游戏的官网、登录、启动器、更新与已确认 CDN。

[`ruleset/InternationalGaming.yaml`](ruleset/InternationalGaming.yaml) 保护可能被宽泛中国规则误判为国内的国际服务，包括 HoYoverse 国际域名和部分海外发行/SDK 端点。

配置在 GlobalMedia 之后、ChinaMax 之前加入 `GEOIP,CN,DIRECT,no-resolve`，用来兜底直接使用中国大陆 IP/UDP 的对局服务器，同时避免额外 DNS 解析，也不会抢在已知国际媒体规则之前。

Steam 采用更窄的处理方式：已确认的中国下载节点进入 `ChinaGaming`；上游 `SteamCN` 仍走 Steam 策略，因为其中同时包含 `steamcontent.com` 等全球共享后缀。

完整审计见[中文版](research/ChinaGaming-audit.md)或[英文版](research/ChinaGaming-audit.en.md)。

## 仓库结构

- `ruleset/`：已提交的 ruleset 快照
- `sources.json`：镜像来源 URL 与目标路径
- `sources.lock.json`：同步信息和 SHA-256
- `local-rulesets.json`：自维护 ruleset 清单
- `scripts/sync.py`：原子下载、格式转换和 provider 生成
- `scripts/validate.py`：离线完整性与配置校验
- `config/`：本地/远程 provider 模板及有序规则示例
- `research/`：可追溯事实来源的分流审计

## 更新

```bash
python3 scripts/sync.py
python3 scripts/validate.py
python3 scripts/public_check.py
git diff --stat
```

同步程序会先下载并验证所有镜像来源，再替换已提交快照。任何一个来源失败，最后一份可用快照都不会被破坏。

GitHub Actions 每天检查一次，只有内容确实变化时才提交。发布后需要在 **Settings → Actions → General → Workflow permissions** 中启用 **Read and write permissions**。

## 准确性与限制

游戏客户端可能直接连接 IP、共享云基础设施、动态 UDP 节点，或只在运行时下发主机名。本仓库覆盖经过验证的公开端点，并提供大陆 GeoIP 兜底，但不能承诺每个游戏、区服和网络环境都完整命中。

高置信新增规则应来自中国大陆客户端的“冷启动 → 登录 → 更新 → 一局对战”链路，并附带 DNS、SNI 或连接日志证据。

## 贡献

参见 [`CONTRIBUTING.md`](CONTRIBUTING.md)。新增规则应说明大陆/国际边界，提供权威证据，并分析整根域名是否会误伤共享或海外服务。

## 许可与第三方内容

本项目自行编写的代码、文档和自维护规则采用 [GNU GPL v2.0](LICENSE)。

镜像文件仍归各自上游作者所有，可能带有额外声明或来源特定条款。再分发前请阅读 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) 和 `sources.json`。本项目与 Mihomo、Clash、各游戏公司及上游规则项目均无隶属或背书关系。

本项目不提供任何保证。使用者应自行核实当地法律、上游条款和实际分流结果。
