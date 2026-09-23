# Proxy Rulesets

常用 AI、Apple、游戏和网络服务的公开分流规则。

**选服务 → 查看说明 → 复制规则地址。全部在这个 GitHub 仓库里完成。**

[服务目录](#服务目录) · [怎么获取](#怎么获取) · [常见问题](#常见问题) · [English](README.en.md)

## 服务目录

点击服务名称查看作用和影响范围；点击「获取地址」进入可复制的地址代码块，点击「查看规则」直接阅读文件。

<!-- SERVICE-CATALOG:START -->
[AI](#ai) · [游戏](#游戏) · [Apple 与网络](#apple-与网络) · [影音](#影音) · [社交](#社交) · [支付与其他](#支付与其他) · [安全与基础](#安全与基础)

### AI

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [Siri AI / Apple Intelligence](services/siri-ai.md) | Siri、听写、云端计算与 AI 扩展的 5 个精确主机。 | [获取地址](services/siri-ai.md#规则地址) · [查看规则](ruleset/SiriAI.yaml) |
| [ChatGPT / OpenAI](services/openai.md) | ChatGPT、OpenAI 与相关连接服务。 | [获取地址](services/openai.md#规则地址) · [查看规则](ruleset/OpenAI_No_Resolve.yaml) |
| [Claude](services/claude.md) | Claude 的上游基础规则。 | [获取地址](services/claude.md#规则地址) · [查看规则](ruleset/Claude_No_Resolve.yaml) |
| [Gemini](services/gemini.md) | Gemini 与相关 Google AI 服务。 | [获取地址](services/gemini.md#规则地址) · [查看规则](ruleset/Gemini_No_Resolve.yaml) |

### 游戏

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [国际游戏](services/international-gaming.md) | 保护已确认的国际服、发行与游戏 SDK。 | [获取地址](services/international-gaming.md#规则地址) · [查看规则](ruleset/InternationalGaming.yaml) |
| [中国游戏](services/china-gaming.md) | 已确认的国服官网、登录、更新和下载服务。 | [获取地址](services/china-gaming.md#规则地址) · [查看规则](ruleset/ChinaGaming.yaml) |
| [Steam](services/steam.md) | Steam 商店、社区与相关全球服务。 | [获取地址](services/steam.md#规则地址) · [查看规则](ruleset/Steam_No_Resolve.yaml) |
| [Steam 下载与蒸汽平台](services/steam-cn.md) | 上游 SteamCN 下载相关规则。 | [获取地址](services/steam-cn.md#规则地址) · [查看规则](ruleset/SteamCN_No_Resolve.yaml) |

### Apple 与网络

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [Apple 服务](services/apple.md) | Apple 通用网络服务。 | [获取地址](services/apple.md#规则地址) · [查看规则](ruleset/Apple_No_Resolve.yaml) |
| [Google](services/google.md) | Google 通用网络服务。 | [获取地址](services/google.md#规则地址) · [查看规则](ruleset/Google_No_Resolve.yaml) |
| [Microsoft](services/microsoft.md) | Microsoft 通用网络服务。 | [获取地址](services/microsoft.md#规则地址) · [查看规则](ruleset/Microsoft_No_Resolve.yaml) |

### 影音

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [YouTube](services/youtube.md) | YouTube 视频及相关资源。 | [获取地址](services/youtube.md#规则地址) · [查看规则](ruleset/YouTube_No_Resolve.yaml) |
| [哔哩哔哩](services/bilibili.md) | 哔哩哔哩服务。 | [获取地址](services/bilibili.md#规则地址) · [查看规则](ruleset/Bilibili_No_Resolve.yaml) |
| [TikTok](services/tiktok.md) | TikTok 内容及相关网络服务。 | [获取地址](services/tiktok.md#规则地址) · [查看规则](ruleset/TikTok_No_Resolve.yaml) |
| [Disney+](services/disney.md) | Disney+ 及相关媒体资源。 | [获取地址](services/disney.md#规则地址) · [查看规则](ruleset/Disney_No_Resolve.yaml) |
| [Netflix](services/netflix.md) | Netflix 内容及相关资源。 | [获取地址](services/netflix.md#规则地址) · [查看规则](ruleset/Netflix_No_Resolve.yaml) |
| [其他国际媒体](services/global-media.md) | 现有上游国际媒体集合。 | [获取地址](services/global-media.md#规则地址) · [查看规则](ruleset/GlobalMedia_Classical_No_Resolve.yaml) |

### 社交

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [Telegram](services/telegram.md) | Telegram 网络连接与资源。 | [获取地址](services/telegram.md#规则地址) · [查看规则](ruleset/Telegram_No_Resolve.yaml) |
| [X / Twitter](services/twitter.md) | X / Twitter 服务及媒体资源。 | [获取地址](services/twitter.md#规则地址) · [查看规则](ruleset/Twitter_No_Resolve.yaml) |
| [Discord](services/discord.md) | Discord 语音、聊天及相关资源。 | [获取地址](services/discord.md#规则地址) · [查看规则](ruleset/Discord_No_Resolve.yaml) |

### 支付与其他

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [PayPal](services/paypal.md) | PayPal 网络服务。 | [获取地址](services/paypal.md#规则地址) · [查看规则](ruleset/PayPal_No_Resolve.yaml) |
| [Stripe](services/stripe.md) | 含 stripe 关键词的网络请求。 | [获取地址](services/stripe.md#规则地址) · [查看规则](ruleset/Stripe_No_Resolve.yaml) |
| [加密资产服务](services/crypto.md) | 上游加密资产服务集合。 | [获取地址](services/crypto.md#规则地址) · [查看规则](ruleset/Crypto_No_Resolve.yaml) |
| [加密资产网页补充](services/crypto-web.md) | 本地维护的加密资产网页补充。 | [获取地址](services/crypto-web.md#规则地址) · [查看规则](ruleset/Crypto.yaml) |

### 安全与基础

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [隐私拦截](services/privacy.md) | 拦截现有上游隐私追踪清单中的连接。 | [获取地址](services/privacy.md#规则地址) · [查看规则](ruleset/Privacy_No_Resolve.yaml) |
| [劫持拦截](services/hijacking.md) | 现有上游劫持防护清单。 | [获取地址](services/hijacking.md#规则地址) · [查看规则](ruleset/Hijacking_No_Resolve.yaml) |
| [中国网络](services/china-max.md) | 上游中国网络综合集合。 | [获取地址](services/china-max.md#规则地址) · [查看规则](ruleset/ChinaMax_Classical_No_Resolve.yaml) |
| [本地网络](services/lan.md) | 现有局域网和保留地址规则。 | [获取地址](services/lan.md#规则地址) · [查看规则](ruleset/Lan_No_Resolve.yaml) |
<!-- SERVICE-CATALOG:END -->

## 怎么获取

1. 在上面的目录中找到服务，也可用浏览器页内搜索查找 ChatGPT、Siri 等名称。
2. 打开服务说明，复制「规则地址」下的整行 URL。
3. 需要文件内容时，点击「查看规则」在 GitHub 阅读，或打开服务页的原始文件链接保存。

复制链接和下载文件都不会修改现有配置。这里提供的是规则，不是节点订阅或完整配置。

## 常见问题

**如何选择？** 只取你需要的服务规则即可。推荐出口和范围限制写在每个服务页里；原有直连、拒绝和可选策略保持区分。

**组合规则时要注意什么？** 规则从上往下匹配，先命中的先生效。保留安全拦截优先、国际游戏先于中国游戏，以及 Siri AI 在 Apple 前、Gemini 在 Google 前。完整顺序见[有序规则](config/rules.yaml)。

**Siri AI 能解锁 Apple 智能吗？** 不能。它只选择网络出口，不改变设备、账号、销售地区或语言资格，也不保证完整覆盖；还可能影响普通 Siri/听写。

**地址打不开怎么办？** 回到服务页点击「查看规则文件」确认内容，或从原始文件链接保存。网络问题仍未解决时，请提交脱敏问题，不要上传私人配置。

## 更多说明

[高级配置参考](docs/advanced.md) · [维护指南](docs/maintainer/README.md) · [贡献](CONTRIBUTING.md) · [安全反馈](SECURITY.md)

公开文件不含节点、订阅或凭证，不收集用户流量。项目自编内容采用 [GPL-2.0](LICENSE)；上游规则保留[来源、署名和许可](THIRD_PARTY_NOTICES.md)。
