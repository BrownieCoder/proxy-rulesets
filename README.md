# Proxy Rulesets

常用 AI、Apple、游戏和网络服务分流规则。已经有自己的代理节点？**选服务，再选客户端。**

[选择服务](#选择服务) · [客户端怎么选](#客户端怎么选) · [常见问题](#常见问题) · [English](README.en.md)

> 安装中心已准备好静态页面，尚未公开上线。本地检出本改造分支后，可打开 `install/index.html`；主分支下载包须待合入后才包含此目录。当前请使用下面的服务教程和现有规则地址。

## 选择服务

下表的“规则地址”可右键或长按复制链接；安装中心提供真正的复制按钮，不必寻找 GitHub 的 Raw 按钮。**这些地址是 Mihomo 规则文件，不是节点订阅，也不能直接粘贴到 Shadowrocket 的模块入口。**

只有能够保持原有分流选择、且地址已发布核验的模块，才显示“一键导入”。AI、Apple、游戏等当前需要手动配置；不会把它们全部改成固定代理。

<!-- INSTALL-TABLE:START -->
### AI

| 服务 | 作用与推荐 | Shadowrocket | ClashX.Meta | Clash Verge Rev / Mihomo | 原始规则 |
| --- | --- | --- | --- | --- | --- |
| [Siri AI / Apple Intelligence](services/siri-ai.md) | Siri、听写、云端计算与 AI 扩展的 5 个精确主机。 按已有 AI 策略选择出口 | [手动教程](services/siri-ai.md#shadowrocket) | [教程](services/siri-ai.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/SiriAI.yaml) | [查看](ruleset/SiriAI.yaml) |
| [ChatGPT / OpenAI](services/openai.md) | ChatGPT、OpenAI 与相关连接服务。 按已有 OpenAI 策略选择出口 | [手动教程](services/openai.md#shadowrocket) | [教程](services/openai.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/OpenAI_No_Resolve.yaml) | [查看](ruleset/OpenAI_No_Resolve.yaml) |
| [Claude](services/claude.md) | Claude 的上游基础规则。 按已有 Claude 策略选择出口 | [手动教程](services/claude.md#shadowrocket) | [教程](services/claude.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Claude_No_Resolve.yaml) | [查看](ruleset/Claude_No_Resolve.yaml) |
| [Gemini](services/gemini.md) | Gemini 与相关 Google AI 服务。 按已有 Gemini 策略选择出口 | [手动教程](services/gemini.md#shadowrocket) | [教程](services/gemini.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Gemini_No_Resolve.yaml) | [查看](ruleset/Gemini_No_Resolve.yaml) |

### 游戏

| 服务 | 作用与推荐 | Shadowrocket | ClashX.Meta | Clash Verge Rev / Mihomo | 原始规则 |
| --- | --- | --- | --- | --- | --- |
| [国际游戏](services/international-gaming.md) | 保护已确认的国际服、发行与游戏 SDK。 只选代理出口 | [手动教程](services/international-gaming.md#shadowrocket) | [教程](services/international-gaming.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/InternationalGaming.yaml) | [查看](ruleset/InternationalGaming.yaml) |
| [中国游戏](services/china-gaming.md) | 已确认的国服官网、登录、更新和下载服务。 直连 | [手动教程](services/china-gaming.md#shadowrocket) | [教程](services/china-gaming.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/ChinaGaming.yaml) | [查看](ruleset/ChinaGaming.yaml) |
| [Steam](services/steam.md) | Steam 商店、社区与相关全球服务。 按已有 Steam 策略选择出口 | [手动教程](services/steam.md#shadowrocket) | [教程](services/steam.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Steam_No_Resolve.yaml) | [查看](ruleset/Steam_No_Resolve.yaml) |
| [Steam 下载与蒸汽平台](services/steam-cn.md) | 上游 SteamCN 下载相关规则。 按已有 Steam 策略选择出口 | [手动教程](services/steam-cn.md#shadowrocket) | [教程](services/steam-cn.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/SteamCN_No_Resolve.yaml) | [查看](ruleset/SteamCN_No_Resolve.yaml) |

### Apple 与网络

| 服务 | 作用与推荐 | Shadowrocket | ClashX.Meta | Clash Verge Rev / Mihomo | 原始规则 |
| --- | --- | --- | --- | --- | --- |
| [Apple 服务](services/apple.md) | Apple 通用网络服务。 默认直连，可选代理 | [手动教程](services/apple.md#shadowrocket) | [教程](services/apple.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Apple_No_Resolve.yaml) | [查看](ruleset/Apple_No_Resolve.yaml) |
| [Google](services/google.md) | Google 通用网络服务。 沿用已有 Google 策略 | [手动教程](services/google.md#shadowrocket) | [教程](services/google.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Google_No_Resolve.yaml) | [查看](ruleset/Google_No_Resolve.yaml) |
| [Microsoft](services/microsoft.md) | Microsoft 通用网络服务。 沿用已有 Microsoft 策略 | [手动教程](services/microsoft.md#shadowrocket) | [教程](services/microsoft.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Microsoft_No_Resolve.yaml) | [查看](ruleset/Microsoft_No_Resolve.yaml) |

### 影音

| 服务 | 作用与推荐 | Shadowrocket | ClashX.Meta | Clash Verge Rev / Mihomo | 原始规则 |
| --- | --- | --- | --- | --- | --- |
| [YouTube](services/youtube.md) | YouTube 视频及相关资源。 按已有国际媒体策略选择出口 | [手动教程](services/youtube.md#shadowrocket) | [教程](services/youtube.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/YouTube_No_Resolve.yaml) | [查看](ruleset/YouTube_No_Resolve.yaml) |
| [哔哩哔哩](services/bilibili.md) | 哔哩哔哩服务。 默认直连，可选代理 | [手动教程](services/bilibili.md#shadowrocket) | [教程](services/bilibili.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Bilibili_No_Resolve.yaml) | [查看](ruleset/Bilibili_No_Resolve.yaml) |
| [TikTok](services/tiktok.md) | TikTok 内容及相关网络服务。 按已有国际媒体策略选择出口 | [手动教程](services/tiktok.md#shadowrocket) | [教程](services/tiktok.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/TikTok_No_Resolve.yaml) | [查看](ruleset/TikTok_No_Resolve.yaml) |
| [Disney+](services/disney.md) | Disney+ 及相关媒体资源。 按已有国际媒体策略选择出口 | [手动教程](services/disney.md#shadowrocket) | [教程](services/disney.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Disney_No_Resolve.yaml) | [查看](ruleset/Disney_No_Resolve.yaml) |
| [Netflix](services/netflix.md) | Netflix 内容及相关资源。 按已有国际媒体策略选择出口 | [手动教程](services/netflix.md#shadowrocket) | [教程](services/netflix.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Netflix_No_Resolve.yaml) | [查看](ruleset/Netflix_No_Resolve.yaml) |
| [其他国际媒体](services/global-media.md) | 现有上游国际媒体集合。 按已有国际媒体策略选择出口 | [手动教程](services/global-media.md#shadowrocket) | [教程](services/global-media.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/GlobalMedia_Classical_No_Resolve.yaml) | [查看](ruleset/GlobalMedia_Classical_No_Resolve.yaml) |

### 社交

| 服务 | 作用与推荐 | Shadowrocket | ClashX.Meta | Clash Verge Rev / Mihomo | 原始规则 |
| --- | --- | --- | --- | --- | --- |
| [Telegram](services/telegram.md) | Telegram 网络连接与资源。 沿用已有 Telegram 策略 | [手动教程](services/telegram.md#shadowrocket) | [教程](services/telegram.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Telegram_No_Resolve.yaml) | [查看](ruleset/Telegram_No_Resolve.yaml) |
| [X / Twitter](services/twitter.md) | X / Twitter 服务及媒体资源。 沿用已有 Twitter 策略 | [手动教程](services/twitter.md#shadowrocket) | [教程](services/twitter.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Twitter_No_Resolve.yaml) | [查看](ruleset/Twitter_No_Resolve.yaml) |
| [Discord](services/discord.md) | Discord 语音、聊天及相关资源。 沿用已有 Discord 策略 | [手动教程](services/discord.md#shadowrocket) | [教程](services/discord.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Discord_No_Resolve.yaml) | [查看](ruleset/Discord_No_Resolve.yaml) |

### 支付与其他

| 服务 | 作用与推荐 | Shadowrocket | ClashX.Meta | Clash Verge Rev / Mihomo | 原始规则 |
| --- | --- | --- | --- | --- | --- |
| [PayPal](services/paypal.md) | PayPal 网络服务。 按已有支付策略选择出口 | [手动教程](services/paypal.md#shadowrocket) | [教程](services/paypal.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/PayPal_No_Resolve.yaml) | [查看](ruleset/PayPal_No_Resolve.yaml) |
| [Stripe](services/stripe.md) | 含 stripe 关键词的网络请求。 按已有支付策略选择出口 | [手动教程](services/stripe.md#shadowrocket) | [教程](services/stripe.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Stripe_No_Resolve.yaml) | [查看](ruleset/Stripe_No_Resolve.yaml) |
| [加密资产服务](services/crypto.md) | 上游加密资产服务集合。 按已有 Crypto 策略选择出口 | [手动教程](services/crypto.md#shadowrocket) | [教程](services/crypto.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Crypto_No_Resolve.yaml) | [查看](ruleset/Crypto_No_Resolve.yaml) |
| [加密资产网页补充](services/crypto-web.md) | 本地维护的加密资产网页补充。 按已有 Crypto 策略选择出口 | [手动教程](services/crypto-web.md#shadowrocket) | [教程](services/crypto-web.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Crypto.yaml) | [查看](ruleset/Crypto.yaml) |

### 安全与基础

| 服务 | 作用与推荐 | Shadowrocket | ClashX.Meta | Clash Verge Rev / Mihomo | 原始规则 |
| --- | --- | --- | --- | --- | --- |
| [隐私拦截](services/privacy.md) | 拦截现有上游隐私追踪清单中的连接。 拒绝连接 | [模块待发布](services/privacy.md#shadowrocket) | [教程](services/privacy.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Privacy_No_Resolve.yaml) | [查看](ruleset/Privacy_No_Resolve.yaml) |
| [劫持拦截](services/hijacking.md) | 现有上游劫持防护清单。 默认拒绝，可选直连 | [手动教程](services/hijacking.md#shadowrocket) | [教程](services/hijacking.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Hijacking_No_Resolve.yaml) | [查看](ruleset/Hijacking_No_Resolve.yaml) |
| [中国网络](services/china-max.md) | 上游中国网络综合集合。 默认直连，可选代理 | [手动教程](services/china-max.md#shadowrocket) | [教程](services/china-max.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/ChinaMax_Classical_No_Resolve.yaml) | [查看](ruleset/ChinaMax_Classical_No_Resolve.yaml) |
| [本地网络](services/lan.md) | 现有局域网和保留地址规则。 直连 | [手动教程](services/lan.md#shadowrocket) | [教程](services/lan.md#clash--mihomo) | [规则地址](https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/Lan_No_Resolve.yaml) | [查看](ruleset/Lan_No_Resolve.yaml) |
<!-- INSTALL-TABLE:END -->

## 客户端怎么选

| 客户端 | 推荐方式 | 一键 | 会不会影响现有配置 |
| --- | --- | --- | --- |
| Shadowrocket（iPhone 小火箭） | [模块与手动教程](docs/clients/shadowrocket.md) | 仅隐私拦截模块已生成，待发布；其他需手动 | 模块不替换节点或主配置，但其规则优先；关闭模块可撤销 |
| ClashX.Meta（macOS） | [将规则接入现有配置](docs/clients/mihomo.md) | 单个规则集不支持 | 完整配置导入会切换配置，同名远程配置可能被替换；不会自动合并规则 |
| Clash Verge Rev（Windows/macOS/Linux） | [复制规则地址、手动接入](docs/clients/mihomo.md) | 单个规则集不支持 | 完整配置通常新增；没有当前配置时可能自动启用；不会自动合并规则 |
| Clash Party（原 Mihomo Party） | [复制规则地址、手动接入](docs/clients/mihomo.md) | 单个规则集不支持 | v2.0.3 通常新增，无当前配置时启用；开发版简易模式另有行为；不会自动合并 |
| 其他 Mihomo 客户端 | [查看通用教程](docs/clients/mihomo.md) | 未统一验证 | Mihomo 是内核，具体操作取决于 App |

能力依据和核验版本见[客户端研究](docs/maintainer/client-capabilities.md)。以上没有把“打开 App”当作“成功安装”，未声称做过真机测试。

## 常见问题

**为什么 ChatGPT 没有一键模块？** 原方案允许你选出口；直接改成固定代理会丢掉选择，还可能让模块越过拦截规则。这里保留原行为，给出手动入口。

**会覆盖节点吗？** 规则文件没有节点或订阅。隐私模块不替换主配置；手动编辑会改变所编辑的配置，先备份。不要把规则地址当作完整配置导入。ClashX.Meta 的完整配置同名导入存在替换风险。

**没有自动打开怎么办？** 支持模块时：复制已发布模块地址 → 打开小火箭的「配置 → 当前配置 → 模块 → 添加模块」→ 粘贴地址并启用。当前模块尚未发布，请等待发布或按[本地验证教程](docs/clients/shadowrocket.md)操作。其他客户端从服务页进入对应教程。

**Siri AI 规则能解锁 Apple 智能吗？** 不能。它只选择网络出口，不改变设备、账号、销售地区和语言资格，也不保证完整覆盖。5 个主机还包括普通 Siri/听写。

**规则不起作用？** 确认正在使用你编辑的配置，再检查规则顺序和实际出口。Mihomo 从上往下使用第一条匹配规则；安全拦截、国际游戏、中国游戏，以及 Siri AI / Apple、Gemini / Google 的先后顺序都要保留。

## 安全与高级入口

本站不收集访问分析，不需要账号，不读取私人配置；公开文件不含节点、订阅或凭证。不需要 MITM、证书或解密。报告问题请只给脱敏信息，不要上传完整配置。

[高级配置](docs/advanced.md) · [维护指南](docs/maintainer/README.md) · [贡献](CONTRIBUTING.md) · [安全反馈](SECURITY.md)

项目自编内容采用 [GPL-2.0](LICENSE)。上游镜像及衍生模块保留来源和署名，使用前请阅读[第三方声明](THIRD_PARTY_NOTICES.md)。本项目与相关客户端、服务及上游作者无隶属或背书关系。
