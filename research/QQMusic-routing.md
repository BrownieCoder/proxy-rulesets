# QQ 音乐公开入口与下载主机分流研究

## 决策与当前状态

`PLANNING`：本次只提交公开来源研究，不改变生产规则、策略组或生成资产。

建议首批仅为下表 3 个精确主机提供 `🎧 QQ 音乐` 独立策略，默认 `DIRECT`，保留手动代理选项。
这 3 个主机已有 ChinaMax 覆盖，新增价值是独立控制，而不是填补完全未覆盖的域名。
共享腾讯主机默认排除，不采用 `qq.com`、`gtimg.com`、`gtimg.cn` 等根域后缀。

## 官方来源与逐主机证据

2026-11-15 未登录读取 [QQ 音乐官方下载页](https://y.qq.com/download/download.html)，HTTP 200，HTML 标题为 QQ 音乐下载页。
以下是公开 HTML 的标签/属性引用事实，不是带账号 App 流量观察，也不表示已执行下载、跟踪重定向或播放音乐。
仅保留主机和不含查询参数的路径；不保存公开下载链接中的签名、完整查询串或原始页面副本。

| 拟纳入精确主机 | 官方来源与实际引用 | 可支持的用途 | 边界 / 置信度 |
| --- | --- | --- | --- |
| `y.qq.com` | [官方下载页](https://y.qq.com/download/download.html)本身；`link[href]` 指向 `/mediastyle/app/download/download_all_c606bc20.css`，`script[src]` 指向 `/component/m/qmfe-ecos-download/index_umd.js`，`img[src]` 指向 `/music/common/upload/T_Y_SOFTWARE/6908936.png` | 官网入口、下载页以及同主机静态/图片资源 | 高：实际 HTML 内容引用；仅本主机，不含其任何子域 |
| `c.y.qq.com` | [官方下载页](https://y.qq.com/download/download.html)中下载按钮的 `a.product__btn.js_stat_down.js_ecos_down[data-url]` 指向 `/cgi-bin/file_redirect.fcg`；其公开参数声明 QQ 音乐客户端安装文件 | 官网声明的客户端文件重定向入口 | 高：实际按钮目标，不是仅预取；未跟随重定向，不把它描述为已核实的播放 API |
| `dldir.y.qq.com` | [官方下载页](https://y.qq.com/download/download.html)中 Windows 下载按钮的 `a.product__btn.js_stat_down.js_ecos_down[data-url]` 指向 `/music/clntupate/QQMusic_YQQWinPCDL.exe` | 官网声明的 Windows 客户端下载入口 | 高：实际按钮目标；未下载可执行文件，不保证下载完整链路 |

来源置信度仅指官方页面使用/声明该主机的证据，不等同于所有权全面审计、所有地区可达保证或原生 App 全链路覆盖。
官网的根入口和新版页面本次未取得可核实的内容引用，因此不从中推断额外主机。

## 明确排除

| 主机或范围 | 观察 / 排除原因 |
| --- | --- |
| `qq.com`、`gtimg.com`、`gtimg.cn` 及整根通配或后缀 | 腾讯共享域名体系，不得为了音乐覆盖扩大到其他产品 |
| `imgcache.qq.com` | 官网实际 CSS [download_all_c606bc20.css](https://y.qq.com/mediastyle/app/download/download_all_c606bc20.css)引用 `/mediastyle/musicprotal/img/icon_sprite.png`；该页面只能证明此路径服务音乐资源，不能证明整个共享主机专属于 QQ 音乐，故默认排除 |
| `dldir1.qq.com`、`dldir1v6.qq.com` | 官网下载链接或公开下载配置中的腾讯下载主机；未证明是 QQ 音乐专用，默认排除 |
| `dlied6.qq.com` | 官网链接路径为 `/invc/qqpcmgr/qudao/` 下的电脑管家安装文件；不是本次音乐服务范围 |
| `service.qq.com`、`www.qq.com`、`www.tencent.com`、`hr.tencent.com` | 客服、腾讯门户、公司与招聘入口，不是 QQ 音乐专用服务 |
| `adver.qq.com` | 广告业务链接，不纳入音乐出口覆盖 |
| `monitor.music.qq.com`、`stat.y.qq.com` | 当前 Privacy 明确覆盖，保持安全拦截优先，不纳入独立 App 规则 |
| 其他追踪主机、仅 DNS 预取/预连接线索、未在官方页面中核实的音频/CDN/API 主机 | 本轮证据不足，不猜测补齐、不按命名推断用途 |

主机级规则不能按 URL 路径区分同一主机上的内容与统计脚本；纳入 `y.qq.com` 不等于移除该主机中的统计代码。
现有与未来的合法 Privacy/Hijacking 拦截必须继续优先。

## 现有 first-match 核实

基线：`4840a9cd0ef6a5507c00492815af7a47a6ce6483`。
读取公开 `sources.json`、`local-rulesets.json` 与 `config/rules.yaml`，复用 `siri_ai.DomainRules`、`entries` 按实际顺序模拟。
模型仅有域名，无 IP/进程信息，跳过 GEOIP/IP 条件，不声称已经执行 Mihomo、DNS 或实际网络出口验证。

| 域名 / 对照 | 当前首条命中与目标 |
| --- | --- |
| `y.qq.com`、`c.y.qq.com`、`dldir.y.qq.com` | `ChinaMax` → `🇨🇳 China-Global` |
| `monitor.music.qq.com`、`stat.y.qq.com` | `Privacy` → `REJECT` |
| `qq.com`、`gtimg.com`、`dldir1.qq.com`、`dldir1v6.qq.com`、`dlied6.qq.com`、`service.qq.com` | `ChinaMax` → `🇨🇳 China-Global` |
| `game.qq.com`、`wegame.gtimg.com` | `ChinaGaming` → `DIRECT` |
| `music.163.com` | `NetEaseMusic` → `🎵 网易云音乐` |
| `child.y.qq.com`、`noty.qq.com` | `ChinaMax` → `🇨🇳 China-Global` |
| `y.qq.com.example.org`、`example.org` | `MATCH` → `🧭 Final` |

计划位置必须在安全/游戏规则之后、Apple/GlobalMedia/GEOIP CN/ChinaMax 等宽泛分流之前，保持既有 SiriAI → Apple 顺序以及其他 App 的已有控制。
当前三个候选未被前置安全、游戏或其他 App 规则抢先匹配；未来合法安全规则若新增覆盖，应优先而非让基础验证失败。

## 最小实施提案（等待批准）

目标：为公开入口与部分资源增加可选的独立出口，不改变非目标主机的现有策略。

1. 仅新增 `QQMusic` 本地 provider，内容固定为上述 3 条 `DOMAIN`，拒绝后缀、重复或额外主机；来源只指向本研究和官方公开页面。
2. 新增 `🎧 QQ 音乐` 的 `select` 策略组，第一项 `DIRECT`，保留 `🚀 节点选择`；一次 active provider 引用，按前述安全/游戏与宽泛 provider 顺序放置。
3. 按现有模式新增 `validate_qq_music(root)`，接入 `validate_tree(root)`；检查固定范围、唯一有效引用、有效顺序标记、DIRECT-first 唯一 select 声明、手动代理项、缺失 provider 清晰报错和未知顶层规则显式拒绝。
4. 真实临时公共 fixture mutation 调用生产 validator，覆盖范围扩大、重复、引用缺失/重复/错误、后置/安全绕过、默认错误、未知规则、非安全抢占、错误安全 target；合法 Privacy/REJECT 或 Hijacking/🚫 Hijacking 未来命中仍应通过同一验收路径。完整公共 fixture 单独验证 tree 入口传递 root。
5. 独立固定 HOSTS 测试防止同源自证；对每个目标的子域、前缀相似域与伪后缀做负向检查，并验证上述安全、腾讯其他产品、游戏、网易云音乐及共享下载/CDN 对照在启用/移除 QQMusic 时首条匹配不变。
6. catalog 文案明确“部分入口/资源：默认直连，可选代理”；通过既有 `generate_catalog.py --write` 离线重建 provider 配置、目录和校验资产，运行完整 tests、validate、public_check 与 diff 检查。不运行网络同步、不改权限/工作流。

预计受影响：`ruleset/QQMusic.yaml`、`local-rulesets.json`、`config/rules.yaml`、`config/proxy-groups.yaml`、`catalog/services.json`、`scripts/validate.py`、独立测试及生成资产；仅在批准后实施。

## 使用与证据边界

仅覆盖上述 3 个主机，不保证原生 App 的登录、搜索、播放、下载重定向全链路、直播或上传。
不改变版权、账号资格、付费订阅或地区限制，不声称播放/地区解锁，也未实测代理对账号风控的影响。
切换代理只影响这 3 个精确主机；其他主机继续使用原策略，可能仍为直连，产生 mixed-egress（混合出口）。
若页面或下载仍失败，应先核对实际失败域名及既有规则命中，提供脱敏域名、预期与实际结果；不要上传完整配置、签名下载 URL、账号数据或私有抓包。
