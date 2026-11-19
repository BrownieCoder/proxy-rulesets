# 顺丰速运公开官网入口分流依据

核实日期：2026-11-19。基线 `70c33529edef85b38eb845a7edf96cccea06067c`。

## 主源与最小范围

仅匿名读取官方公开介绍页和 App Store 开发者链接，不登录、不填写运单、不查询个人订单，不进入寄件、付款或账户流程，不下载客户端，不保存原始网页、响应头或任何用户数据。

| 精确主机 / 对照 | 主源与实际观察 | 决定、用途及置信度 |
| --- | --- | --- |
| `www.sf-express.com` | [中国内地官网](https://www.sf-express.com/chn/sc/)本轮规范为同主机 `/chn/sc`，页面标识中国内地；[官方渠道公告](https://www.sf-express.com/chn/sc/notice/329)明确声明官网地址，并分别介绍顺丰速运 App。国内 [App Store 页面](https://apps.apple.com/cn/app/id899529698)的真实开发者隐私链接也指向同主机的[隐私页面](https://www.sf-express.com/chn/sc/privacy) | 接受唯一 `DOMAIN`，`SFExpress` / `sf-express` / `📦 顺丰速运`，生活服务，默认 DIRECT，保留手动代理与 Final。高置信公开入口身份；不是 Apple 对主机独占性或业务可用性的认证。隐私页本轮仅有框架内容，不声称读到完整正文 |
| 同一目标主机的国际 / 企业路径 | 官网实际国际产品链接指向[国际标快页面](https://www.sf-express.com/chn/sc/express/intl/int-standard)，首页也展示企业、仓储及科技等业务 | 同主机这些路径也受规则影响，不能宣称仅控制中国大陆 App、仅影响国内快递，或所有国际流量不变。主机级规则不能按地区、产品或路径隔离 |
| `www-static.sf-express.com` | 上述官网的真实图片引用 | 不纳入：共享官网资源主机，不把部分素材关联当作完整 App 必需性或主机独占证据；未请求图片文件 |
| `www.sf-international.com` | 国际标快页面有指向该主机的实际增值服务链接；[独立国际官网](https://www.sf-international.com/)本轮转到同主机 `/cn/sc` | 不纳入：独立国际站与相关请求保持原规则，但这不意味着目标 `www.sf-express.com` 内的国际产品路径保持原出口 |
| `www.sf-laas.com` | 中国内地官网科技服务入口实际指向此主机 | 不纳入：不同科技业务入口，不代表大陆寄查件 App 的必要连接；未访问其业务系统 |
| `www.sf-airlines.com` | [顺丰航空官方介绍](https://www.sf-airlines.com/about/index.html)展示独立航空业务，并在页尾链接顺丰速运、科技和快运网站 | 不纳入：集团关联不等于本 App 分流范围，未进入货物追踪或航班业务 |

根地址 `https://www.sf-express.com/` 在本轮网页工具中没有可读正文；不把它描述成已证实的首页跳转、HTTP 故障或地区判定。中国内地路径及官方渠道公告已足以支持上述精确入口，不依赖根地址的动态行为。

## 基线首匹配与影响

使用实际公开 manifests、payload 和有序模板，按既有无 IP / 进程元数据的域名模型模拟：唯一目标、裸根 `sf-express.com`、上述静态 / 国际 / 科技 / 航空主机均为 `ChinaMax → 🇨🇳 China-Global`。新策略提供独立出口选择，不是首次覆盖，也不证明现有连接有故障。

仅目标全部路径改由可选组处理。裸根、其他子域、共享资源、独立国际和其他集团主机不增加规则；不添加任何 `sf-express.com` 后缀、通配符、推测的 API、登录、运单、支付、下单、推送或文件端点。命名负控 `child.www.sf-express.com`、`notwww.sf-express.com` 仍为 ChinaMax，`www.sf-express.com.example.org` 为 Final；只是模型边界，不查询这些名称的存在性。

其他请求沿原策略，手动代理可能产生混合出口。本批不是完整原生 App、寄件、查件、订单、实时轨迹、登录、付款或国际链路控制；不保证账号 / 地区资格、业务成功、送达时效、网络性能或服务可用性。未测试真实 App、DNS、GeoIP、UDP、私人账户或任何快件。

## 接入与验证约定

1. 唯一活动引用位于基线全部 25 个 App（含 WPS Office、飞书、钉钉、夸克）之后、Quark 之后、SiriAI 之前。保留拒绝 / 安全、游戏、旧规则相对顺序、Gemini 与 Google、MATCH 和所有已有出口选项。
2. 新增自身 `validate_sf_express(root)` 与一次 tree 调用，不修改旧函数或共享解析器；在公共策略组结构测试的直接入口列表追加本 App。固定精确范围、唯一引用、DIRECT-first select / 代理 / Final、先后顺序、真实首匹配与非目标对照。
3. 用完整公开临时 fixture 先证明正向通过，再验证范围 / 引用、25 前驱与后继、严格策略组形状和合法字面量、安全合法更新与非安全遮蔽、provider、未知 / 不完整 / 空白字段、前置 IP 条件、规则及策略组重复根、UTF-8。按具体变体区分共享结构诊断与 App 语义诊断，不将任意异常当作通过。
4. 只通过现有离线生成器维护 providers、目录页及 hash；运行专项、完整测试、默认验证、公开检查、生成一致性与 diff 检查，结果绑定精确版本。保留来源 / 镜像 / 许可 / 工作流 / 依赖与权限，不运行网络同步，不读取私人配置。

## English scope summary

Include only the exact public portal `www.sf-express.com`, with an optional DIRECT-first SFExpress group. The mainland portal, official channel notice and domestic App Store developer privacy link support its identity. All paths on this host follow the group, including its international-product and enterprise pages: this cannot isolate mainland-App traffic or preserve every international request. Separate international, static-resource, technology and airline hosts stay excluded. Other requests retain their routes, allowing mixed egress. This is not native-app, account, shipment, tracking, payment or international end-to-end coverage, and guarantees no availability, delivery outcome or eligibility. No personal shipment, login, order, payment or private configuration was accessed. Verification uses public disposable fixtures and an offline domain model.
