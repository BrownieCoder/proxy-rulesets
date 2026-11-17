# 钉钉公开入口精确分流研究

## 状态与建议范围

研究日期：2026-11-18。已接受范围仅为下述一个精确主机，实施不扩大共享资源或业务主机范围。保留基线 `74b4640cfb0d8cef4395fb199f8e9f8903fcd84e` 的 49 services、24 mirrored / 25 local 和 557 项既有测试合同；验证使用 Python 3.12 / PyYAML 6.0.2。

首批仅 `DOMAIN,www.dingtalk.com`：provider `DingTalk`、目录 id `dingtalk`、分类“办公”、独立 `💬 钉钉` literal select，DIRECT-first，保留 `🚀 节点选择` 与 `🧭 Final`。新增价值是官网入口独立选择出口，不是此前完全没有覆盖，也不是完整钉钉 App 分流。

## Primary evidence 与排除边界

仅匿名读取[钉钉官网](https://www.dingtalk.com/)公开 HTML；普通 HTTPS 请求 HTTP 200，标题“钉钉，AI时代工作方式”，网页提取结果与直接读取均能核实品牌和入口。没有 Cookie、登录、下载、会议或业务操作；不执行脚本或请求页面声明的资源，不保存原始页面、查询值、用户字段或私人流量。

| 主机 | 官网实际声明 / 支持用途 | 决定与置信度 |
| --- | --- | --- |
| `www.dingtalk.com` | 已实际读取的官方首页；正文展示钉钉、千问办公、AI 听记 / 表格 / 会议等入口或按钮文案 | 已接受，仅官网精确主机；高置信公开身份，不代表这些产品 / 业务已运行或全部属于该主机 |
| `gw.alicdn.com`、`img.alicdn.com` | 实际 `img[src]`，路径位于 `/imgextra/` | 排除共享阿里图片主机，不因钉钉使用部分素材而接管整台主机 |
| `cloud.video.taobao.com` | 实际 `video[src]`，路径位于 `/vod/` | 排除共享视频资源；只观察声明，未获取、播放或检查媒体文件 |

本次没有取得可支持额外精确主机的公开页面链接；不根据名称猜客户端、下载、登录、API、聊天或会议端点。不收整个 `dingtalk.com`、`alicdn.com`、`taobao.com` 或阿里命名空间；其他办公品牌仅作非目标对照，不声称官网引用过它们。

精确主机仍覆盖所有路径：同主机未来或现有的产品宣传、下载介绍、登录 / 业务外壳、追踪等路径都可能随该组出口，无法按路径分离。只确认公开官网，不把首页文案当作这些功能或追踪脚本存在 / 可用的证明。

## 当前 first-match 与影响

读取公共 manifests、ruleset 和实际有序模板，用既有 `DomainRules` 模拟：`www.dingtalk.com` 当前为 `ChinaMax → 🇨🇳 China-Global`，更早安全、游戏和 21 个已合 App 未抢占。共享图片 / 视频主机及裸根 `dingtalk.com` 也仍走 ChinaMax；不因此把它们加入本组。

固定负向边界拟包含上述三个资源主机、`dingtalk.com` / `alicdn.com` / `taobao.com`、淘宝 / 阿里云盘 / 闲鱼 / 优酷官网、飞书 / 企业微信官网边界、Siri、国际游戏精确例外、Gemini、Datadog 通用平台、`example.org`，以及目标的子域 / 相似前缀 / 伪后缀。它们须保持原首匹配，不推断为实际钉钉流量。

可选代理只影响列出的一个主机；被排除的资源和其他业务请求沿用原策略，会形成 mixed egress。不保证登录、聊天、组织管理、会议、客户端、下载、设备或企业网络可用性，不解锁账号 / 组织 / 地区资格。切代理后如遇登录或地区异常，可恢复 DIRECT 排查；这是条件提示，未实测风控或修复效果。模型无 IP / 进程元数据，也未实测 DNS、GeoIP、UDP 或真实客户端。

## 已接受的最小实施范围

1. 只添加固定一条 DOMAIN 的本地规则、manifest、catalog、策略组及唯一活动引用；新引用位于全部 21 个已合 App（直到 Youku）之后、SiriAI 之前。保留安全 / 游戏、全部旧规则相对顺序、Gemini 与 FINAL/MATCH，约束 SiriAI、Apple、五媒体、Gemini、GlobalMedia、GEOIP CN、ChinaMax 为后继。
2. 仅新增 `validate_dingtalk(root)` 与一次真实 tree hook；复用未修改的 `app_policy` / `public_rules`。固定 exact / 重复 / 引用 / 顺序 / DIRECT、代理、Final；未知或不完整条件（含全空白字段）、前置 IP、provider 冲突 / 缺失均清晰 fail closed；所有文本显式 UTF-8。不改旧 helper、共享模块、源、源锁、镜像、权限或工作流。
3. 新测试使用独立固定 HOSTS 和本 App 的负控，不复制其他 App 的控制集合。真实完整公共 fixture 先正向通过；再检验 scope、引用、21 前驱 / 后继、策略默认 / Final、复杂 YAML、合法 literal 形式、UTF-8、未知 / 空白 / IP、provider 和重复根键。helper 严格自己的诊断；完整树允许较早门禁给出正确原因的 ValueError，不硬锁最后一个 App 名称，也不把 IndexError 当通过。
4. 实际首匹配接受本组或正确 Privacy/REJECT、Hijacking/劫持组，拒绝非安全遮蔽与错误目标；未来合法安全更新不应使正常验收失败。验证所有非目标启用 / 关闭本组时不变，并保持旧源码 / 资产保护。
5. 只用已有离线 `generate_catalog --write` 更新派生资产；Python 3.12 / PyYAML 6.0.2 验证针对性、默认、生成一致性、diff 与完整测试，完整结果对应固定候选提交。不运行网络同步；发布遵循仓库交付门禁。

风险主要是同主机全路径和混合出口；证据不足时缩小范围，不添加共享根或未观察接口。研究与实施分开保存，生产仅采用上述已接受范围。

## English scope summary

The accepted scope is one exact official public entry, `www.dingtalk.com`, with a DIRECT-first `💬 钉钉` select group and manual proxy / Final options. Anonymous official HTML establishes the portal; actual shared Alibaba images and a Taobao video declaration remain excluded, and no linked resource, download, login or business endpoint was requested.
All paths on the listed host follow the group. Other resources and business hosts retain their routes, so mixed egress is expected. This is not complete DingTalk/native-app/chat/meeting/download coverage, nor an account, organization or region unlock. Implementation preserves all 21 existing App routes, security/gaming/Gemini ordering and unchanged shared validators, permissions and provenance.
