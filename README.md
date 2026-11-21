# Proxy Rulesets

常用 AI、Apple、游戏和网络服务的公开分流规则。

**选服务 → 查看说明 → 复制规则地址。全部在这个 GitHub 仓库里完成。**

[服务目录](#服务目录) · [怎么获取](#怎么获取) · [常见问题](#常见问题) · [English](README.en.md)

## 服务目录

点击服务名称查看作用和影响范围；点击「获取地址」进入可复制的地址代码块，点击「查看规则」直接阅读文件。

<!-- SERVICE-CATALOG:START -->
[AI](#ai) · [游戏](#游戏) · [Apple 与网络](#apple-与网络) · [影音](#影音) · [购物](#购物) · [出行](#出行) · [社交](#社交) · [生活服务](#生活服务) · [支付与其他](#支付与其他) · [办公](#办公) · [工具](#工具) · [安全与基础](#安全与基础)

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
| [爱奇艺 / iQIYI](services/iqiyi.md) | 仅官网和客户端介绍页共用的 www.iqiyi.com 精确公开入口。 | [获取地址](services/iqiyi.md#规则地址) · [查看规则](ruleset/IQIYI.yaml) |
| [快手 / Kuaishou](services/kuaishou.md) | 快手品牌官网和移动跳转入口，共 2 个精确主机，仅控制部分公开入口。 | [获取地址](services/kuaishou.md#规则地址) · [查看规则](ruleset/Kuaishou.yaml) |
| [腾讯视频 / Tencent Video](services/tencent-video.md) | 桌面、移动和公开会员入口的 4 个精确主机，不代表完整播放链路。 | [获取地址](services/tencent-video.md#规则地址) · [查看规则](ruleset/TencentVideo.yaml) |
| [QQ 音乐](services/qq-music.md) | QQ 音乐官网、同主机资源及声明的下载入口，共 3 个精确主机。 | [获取地址](services/qq-music.md#规则地址) · [查看规则](ruleset/QQMusic.yaml) |
| [网易云音乐](services/netease-music.md) | 官网及部分静态、图片资源的 8 个精确主机。 | [获取地址](services/netease-music.md#规则地址) · [查看规则](ruleset/NetEaseMusic.yaml) |
| [哔哩哔哩](services/bilibili.md) | 哔哩哔哩服务。 | [获取地址](services/bilibili.md#规则地址) · [查看规则](ruleset/Bilibili_No_Resolve.yaml) |
| [抖音](services/douyin.md) | 抖音官网与公开页面实际使用的静态资源，共 3 个精确主机。 | [获取地址](services/douyin.md#规则地址) · [查看规则](ruleset/Douyin.yaml) |
| [TikTok](services/tiktok.md) | TikTok 内容及相关网络服务。 | [获取地址](services/tiktok.md#规则地址) · [查看规则](ruleset/TikTok_No_Resolve.yaml) |
| [Disney+](services/disney.md) | Disney+ 及相关媒体资源。 | [获取地址](services/disney.md#规则地址) · [查看规则](ruleset/Disney_No_Resolve.yaml) |
| [Netflix](services/netflix.md) | Netflix 内容及相关资源。 | [获取地址](services/netflix.md#规则地址) · [查看规则](ruleset/Netflix_No_Resolve.yaml) |
| [其他国际媒体](services/global-media.md) | 现有上游国际媒体集合。 | [获取地址](services/global-media.md#规则地址) · [查看规则](ruleset/GlobalMedia_Classical_No_Resolve.yaml) |
| [优酷 / Youku](services/youku.md) | 优酷官网一个已核实精确主机；不包含共享资源或完整播放链路。 | [获取地址](services/youku.md#规则地址) · [查看规则](ruleset/Youku.yaml) |
| [芒果TV / Mango TV](services/mango-tv.md) | 仅 www.mgtv.com 一个精确公开入口，包含同主机客户端介绍页。 | [获取地址](services/mango-tv.md#规则地址) · [查看规则](ruleset/MangoTV.yaml) |
| [猫眼 / Maoyan](services/maoyan.md) | 仅 www.maoyan.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/maoyan.md#规则地址) · [查看规则](ruleset/Maoyan.yaml) |
| [斗鱼 / DouYu](services/douyu.md) | 仅 m.douyu.com 的移动直播网页及打开 App 入口，不代表完整 App 流量。 | [获取地址](services/douyu.md#规则地址) · [查看规则](ruleset/DouYu.yaml) |

### 购物

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [京东 / JD](services/jd.md) | 京东移动商城、App 入口和图片静态资源的 8 个精确主机。 | [获取地址](services/jd.md#规则地址) · [查看规则](ruleset/JD.yaml) |
| [淘宝 / Taobao](services/taobao.md) | 淘宝官网、移动跳转、客户端下载与商品网页入口的 4 个精确主机。 | [获取地址](services/taobao.md#规则地址) · [查看规则](ruleset/Taobao.yaml) |
| [闲鱼 / Xianyu](services/xianyu.md) | 闲鱼官网、根域跳转及公开条款入口的 3 个精确主机。 | [获取地址](services/xianyu.md#规则地址) · [查看规则](ruleset/Xianyu.yaml) |
| [拼多多 / Pinduoduo](services/pinduoduo.md) | 拼多多公开官网、移动商城入口及图片资源的 5 个精确主机。 | [获取地址](services/pinduoduo.md#规则地址) · [查看规则](ruleset/Pinduoduo.yaml) |
| [得物 / Dewu](services/dewu.md) | 仅 dewu.com 与 www.dewu.com 两个精确公开官网入口。 | [获取地址](services/dewu.md#规则地址) · [查看规则](ruleset/Dewu.yaml) |
| [盒马 / Freshippo](services/freshippo.md) | 仅 www.freshhema.com、www.freshippo.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/freshippo.md#规则地址) · [查看规则](ruleset/Freshippo.yaml) |
| [叮咚买菜 / Dingdong Maicai](services/dingdong-maicai.md) | 仅 www.100.me 的官网及同主机 App 下载入口，不代表完整 App 流量。 | [获取地址](services/dingdong-maicai.md#规则地址) · [查看规则](ruleset/DingdongMaicai.yaml) |

### 出行

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [铁路12306 / Railway 12306](services/railway-12306.md) | 官方门户、客户端介绍与声明的 Android 下载入口，共 3 个精确主机。 | [获取地址](services/railway-12306.md#规则地址) · [查看规则](ruleset/Railway12306.yaml) |
| [携程旅行 / Ctrip](services/ctrip.md) | 携程官网、移动、App 推广及机酒火车度假网页的 7 个精确入口主机。 | [获取地址](services/ctrip.md#规则地址) · [查看规则](ruleset/Ctrip.yaml) |
| [百度地图 / Baidu Map](services/baidu-map.md) | 百度地图官网、JSAPI 入口与网页资源的 4 个精确主机。 | [获取地址](services/baidu-map.md#规则地址) · [查看规则](ruleset/BaiduMap.yaml) |
| [高德地图 / AMap](services/amap.md) | 高德官网、移动入口与公开地图接口的六个精确主机。 | [获取地址](services/amap.md#规则地址) · [查看规则](ruleset/Amap.yaml) |
| [滴滴出行 / DiDi](services/didi.md) | 仅 www.didichuxing.com 与 www.didiglobal.com 两个精确公开官网入口。 | [获取地址](services/didi.md#规则地址) · [查看规则](ruleset/Didi.yaml) |
| [腾讯地图 / Tencent Map](services/tencent-map.md) | 仅 map.qq.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/tencent-map.md#规则地址) · [查看规则](ruleset/TencentMap.yaml) |
| [飞猪 / Fliggy](services/fliggy.md) | 仅 www.fliggy.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/fliggy.md#规则地址) · [查看规则](ruleset/Fliggy.yaml) |
| [同程旅行 / Tongcheng Travel](services/tongcheng-travel.md) | 仅 m.ly.com 的移动旅行网页及 App 导流入口，不代表完整 App 流量。 | [获取地址](services/tongcheng-travel.md#规则地址) · [查看规则](ruleset/TongchengTravel.yaml) |

### 社交

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [知乎](services/zhihu.md) | 知乎网页、公开前端 API 配置及图片静态资源的 8 个精确主机。 | [获取地址](services/zhihu.md#规则地址) · [查看规则](ruleset/Zhihu.yaml) |
| [小红书 / RedNote](services/xiaohongshu.md) | 小红书、RedNote 与专用图片、视频资源的四个第一方根域。 | [获取地址](services/xiaohongshu.md#规则地址) · [查看规则](ruleset/Xiaohongshu.yaml) |
| [豆瓣](services/douban.md) | 豆瓣公开网页、登录入口与图像和静态资源的 8 个精确主机。 | [获取地址](services/douban.md#规则地址) · [查看规则](ruleset/Douban.yaml) |
| [Telegram](services/telegram.md) | Telegram 网络连接与资源。 | [获取地址](services/telegram.md#规则地址) · [查看规则](ruleset/Telegram_No_Resolve.yaml) |
| [X / Twitter](services/twitter.md) | X / Twitter 服务及媒体资源。 | [获取地址](services/twitter.md#规则地址) · [查看规则](ruleset/Twitter_No_Resolve.yaml) |
| [Discord](services/discord.md) | Discord 语音、聊天及相关资源。 | [获取地址](services/discord.md#规则地址) · [查看规则](ruleset/Discord_No_Resolve.yaml) |
| [微信 / WeChat](services/wechat.md) | 仅 weixin.qq.com 一个已核实的官方公开入口。 | [获取地址](services/wechat.md#规则地址) · [查看规则](ruleset/WeChat.yaml) |
| [微博 / Weibo](services/weibo.md) | 仅 weibo.com 与 www.weibo.com 两个精确公开入口主机。 | [获取地址](services/weibo.md#规则地址) · [查看规则](ruleset/Weibo.yaml) |
| [腾讯 QQ / Tencent QQ](services/tencent-qq.md) | 仅 im.qq.com 一个精确公开入口主机，不是完整 QQ 客户端分流。 | [获取地址](services/tencent-qq.md#规则地址) · [查看规则](ruleset/TencentQQ.yaml) |

### 生活服务

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [美团](services/meituan.md) | 官网、消费和外卖入口与部分资源的 7 个精确主机。 | [获取地址](services/meituan.md#规则地址) · [查看规则](ruleset/Meituan.yaml) |
| [BOSS 直聘 / BOSS Zhipin](services/boss-zhipin.md) | BOSS 直聘官网与官网链接的 App 入口页，共两个精确公开主机。 | [获取地址](services/boss-zhipin.md#规则地址) · [查看规则](ruleset/BossZhipin.yaml) |
| [顺丰速运 / SF Express](services/sf-express.md) | 仅 www.sf-express.com 一个公开官网入口，不是完整寄查件 App 分流。 | [获取地址](services/sf-express.md#规则地址) · [查看规则](ruleset/SFExpress.yaml) |
| [货拉拉 / Huolala](services/huolala.md) | 仅 www.huolala.cn 的精确公开入口，不是完整 App 分流。 | [获取地址](services/huolala.md#规则地址) · [查看规则](ruleset/Huolala.yaml) |
| [微信读书 / WeRead](services/wechat-reading.md) | 仅 weread.qq.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/wechat-reading.md#规则地址) · [查看规则](ruleset/WeChatReading.yaml) |
| [肯德基中国 / KFC China](services/kfc-china.md) | 仅 www.kfc.com.cn 的中国官网和同主机 App 下载介绍页，不代表完整 App 流量。 | [获取地址](services/kfc-china.md#规则地址) · [查看规则](ruleset/KFCChina.yaml) |

### 支付与其他

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [阿里云盘 / AliPan](services/alipan.md) | 阿里云盘当前与兼容官网的 2 个精确公开入口主机。 | [获取地址](services/alipan.md#规则地址) · [查看规则](ruleset/AliPan.yaml) |
| [百度网盘](services/baidu-pan.md) | 百度网盘官网入口及静态资源的 2 个精确主机。 | [获取地址](services/baidu-pan.md#规则地址) · [查看规则](ruleset/BaiduPan.yaml) |
| [PayPal](services/paypal.md) | PayPal 网络服务。 | [获取地址](services/paypal.md#规则地址) · [查看规则](ruleset/PayPal_No_Resolve.yaml) |
| [Stripe](services/stripe.md) | 含 stripe 关键词的网络请求。 | [获取地址](services/stripe.md#规则地址) · [查看规则](ruleset/Stripe_No_Resolve.yaml) |
| [加密资产服务](services/crypto.md) | 上游加密资产服务集合。 | [获取地址](services/crypto.md#规则地址) · [查看规则](ruleset/Crypto_No_Resolve.yaml) |
| [加密资产网页补充](services/crypto-web.md) | 本地维护的加密资产网页补充。 | [获取地址](services/crypto-web.md#规则地址) · [查看规则](ruleset/Crypto.yaml) |

### 办公

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [WPS Office](services/wps-office.md) | WPS Office 官网与 Windows、Mac、Linux 产品入口的 4 个精确主机。 | [获取地址](services/wps-office.md#规则地址) · [查看规则](ruleset/WPSOffice.yaml) |
| [飞书 / Feishu](services/feishu.md) | 仅 www.feishu.cn 一个已核实的国内公开入口主机。 | [获取地址](services/feishu.md#规则地址) · [查看规则](ruleset/Feishu.yaml) |
| [钉钉 / DingTalk](services/dingtalk.md) | 仅 www.dingtalk.com 一个已核实的官网公开入口。 | [获取地址](services/dingtalk.md#规则地址) · [查看规则](ruleset/DingTalk.yaml) |
| [企业微信 / WeCom](services/wecom.md) | 仅 work.weixin.qq.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/wecom.md#规则地址) · [查看规则](ruleset/WeCom.yaml) |
| [腾讯会议 / Tencent Meeting](services/tencent-meeting.md) | 仅 meeting.tencent.com、meeting.qq.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/tencent-meeting.md#规则地址) · [查看规则](ruleset/TencentMeeting.yaml) |
| [网易邮箱大师 / NetEase Mail Master](services/netease-mail-master.md) | 仅 dashi.163.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/netease-mail-master.md#规则地址) · [查看规则](ruleset/NetEaseMailMaster.yaml) |
| [腾讯文档 / Tencent Docs](services/tencent-docs.md) | 仅 docs.qq.com 的官网及同主机在线文档网页，不代表完整 App 流量。 | [获取地址](services/tencent-docs.md#规则地址) · [查看规则](ruleset/TencentDocs.yaml) |

### 工具

| 服务 | 作用 | 获取 |
| --- | --- | --- |
| [夸克 / Quark](services/quark.md) | 夸克官网与官网声明的网盘门户，共 2 个精确公开入口。 | [获取地址](services/quark.md#规则地址) · [查看规则](ruleset/Quark.yaml) |
| [美图秀秀 / Meitu Xiuxiu](services/meitu-xiuxiu.md) | 仅 xiuxiu.meitu.com、www.meituxiuxiu.com 的精确公开入口，不是完整 App 分流。 | [获取地址](services/meitu-xiuxiu.md#规则地址) · [查看规则](ruleset/MeituXiuXiu.yaml) |

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
