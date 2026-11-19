# BOSS 直聘公开入口精确分流依据

核实日期：2026-11-19。公开基线：`70c33529edef85b38eb845a7edf96cccea06067c`。

| 精确主机 | 官方依据 | 目标、置信度与影响 |
| --- | --- | --- |
| `www.zhipin.com` | [BOSS 直聘公开官网](https://www.zhipin.com/)展示求职、招聘入口；[国内 App Store 列表](https://apps.apple.com/cn/app/id887314963)的开发者网站链接指向该主机 | 高置信公开入口；默认 `DIRECT`，可选现有手动代理与 Final。同主机全部路径受影响，不能按产品、用户或路径区分。开发者声明不是 Apple 对客户端端点的认证 |
| `app.zhipin.com` | 官网 APP 导航实际链接到[公开 App 介绍及下载入口页](https://app.zhipin.com/)，匿名网页正文可读 | 高置信官方 App 入口页；同一策略，影响同主机全部路径。没有点击下载或请求安装包，不推断整个下载链路 |

只读公开匿名网页，没有登录、提交简历、发起聊天、测试下载、运行客户端或读取代理配置。两个主机在基线的离线域名首匹配均为 `ChinaMax → 🇨🇳 China-Global`；新增策略提供独立选择出口，并非此前未匹配，也不证明原出口有故障。

## 排除与限制

- 不纳入 `zhipin.com`、`bosszhipin.com` 或 `kanzhun.com` 整个后缀。保持 `ir.zhipin.com`、`about.zhipin.com`、`static.zhipin.com`、`img.bosszhipin.com`、`youle.zhipin.com`、店长直聘与 OfferToday 等其他公开主机原策略。主页的链接或图片引用不意味着需要接管同根域或资源服务。
- 不猜测额外 API、聊天、认证、简历文件、招聘者或安装包主机。若业务请求就在两个已列主机上，其路径仍跟随本组；其他主机不变，可能形成混合出口。
- 不保证原生 App、登录、直聊、投递、文件传输、下载安装、账号、招聘资格或地区可用性。DNS、GeoIP、UDP、真实客户端及代理连通性未实测。

## 接入与验证

采用 `BossZhipin`、目录 id `boss-zhipin`、策略组 `💼 BOSS直聘`（DIRECT、节点选择、Final）。新增引用位于 25 个旧 App（截至夸克）之后、Siri AI 与宽泛策略之前，保留拒绝、安全、国际游戏优先、旧规则相对顺序与 MATCH。验证固定 host 集合、精确组成员顺序、实际首匹配、安全例外与非目标边界，并基于临时公开完整配置测试异常结构。派生资产使用已有离线生成器。

## English scope

Two exact public hostnames only: the official recruitment homepage, corroborated by the developer link in the Chinese App Store, and the public app landing page linked from that homepage. Both are DIRECT-first with existing manual proxy and Final choices. All paths on the two hosts follow that policy; assets and other hosts keep their existing routes. This is not whole-app, auth, messaging, resume, download, account or regional coverage, and mixed egress is possible. No private inputs or real client sessions were used.
