# 小红书 / RedNote 分流依据

## 目标与边界

为小红书提供独立的 `📕 小红书 / REDnote` 可选策略，默认 `DIRECT`，也可手动选代理。
这四个根域已被 ChinaMax 覆盖；本次增加的是独立控制和更早匹配，不是宣称此前没有覆盖。
规则保持在 Privacy / Hijacking 和游戏规则之后、通用 Apple / 媒体 / ChinaMax 之前；安全拦截仍然优先。

## 接受的范围

| 根域 | 公开依据 | 用途 / 目标 | 置信度与影响范围 |
| --- | --- | --- | --- |
| `xiaohongshu.com` | [官方网站](https://www.xiaohongshu.com/)及[隐私政策](https://agree.xiaohongshu.com/h5/terms/ZXXY20230227002/-1) | 官网及第一方服务，默认直连 | 高；包含该根域的所有子域 |
| `rednote.com` | [RedNote 官网](https://www.rednote.com/)及[创作中心](https://creator.rednote.com/) | RedNote 第一方服务，默认直连 | 高；包含该根域的所有子域 |
| `xhscdn.com` | 上述官网 HTML 中的 `fe-static.xhscdn.com`、`sns-webpic-qc.xhscdn.com` 等资源引用 | 专用图片、静态及视频资源，默认直连 | 高；包含该专用 CDN 根域的所有子域 |
| `xhscdn.net` | 上述官网 HTML 中的 `sns-video-hw.xhscdn.net` 引用 | 专用视频资源，默认直连 | 中高；包含该专用 CDN 根域的所有子域 |

2026-11-13 重新读取小红书和 RedNote 的公开网页，确认仍有上述资源主机引用。
这证明页面使用这些服务域名，不证明每个子域的独立所有权或所有 App 请求都已覆盖。
未扩展到共享云厂商/CDN 根域，也未添加未核实的其他 RedNote 品牌域名。

## 验证边界

默认直连是可调整的网络出口建议；可用性取决于 ISP、地区和服务变化。
本次没有读取私人节点或订阅，没有使用登录账户做 App、登录、上传或视频播放实测。
离线测试覆盖域名首条匹配、安全优先、相似域名边界与策略默认值；不代表 DNS、GeoIP、UDP 或真实设备端到端验证。
