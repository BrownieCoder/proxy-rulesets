# 携程公开入口精确分流依据

## 决策与证据

核实日期：2026-11-15。只收录以下七个精确 `DOMAIN`，使用独立 `🧳 携程` 策略，默认直连，可手动选择代理。它们已由现有 ChinaMax 覆盖；新增的是独立选择，不是此前完全无法匹配。

公开来源为[携程官网](https://www.ctrip.com/)及[携程无线官网](https://m.ctrip.com/)，后者本次跳转至 `/html5/`。采集只读取匿名公开 HTML：桌面页标题为“携程旅行网:酒店预订,机票预订查询,旅游度假,商旅管理”，移动页标题标识携程无线官网。没有登录、查询个人行程、发起预订或传输账户数据。

| 精确主机 | 官方页面中的实际证据 | 用途与目标 | 置信度 / 影响范围 |
| --- | --- | --- | --- |
| `www.ctrip.com` | 官网页面本身及首页链接 | 桌面公开入口；默认直连，可选代理 | 高：只匹配该主机全部路径，不包含子域 |
| `m.ctrip.com` | 移动官网实际页面；桌面官网链接 `/webapp/qualifications-rules/index` 等 | 移动公开入口；默认直连，可选代理 | 高：同主机的不同业务路径也受同一策略影响 |
| `app.ctrip.com` | 桌面官网实际 `<a href>` 目标主机，路径 `/` | App 推广/下载入口；默认直连，可选代理 | 高：官网关联证据，不代表安装包或原生 App 请求完整覆盖 |
| `hotels.ctrip.com` | 桌面官网实际链接 `/`、`/international/` 等 | 酒店网页入口；默认直连，可选代理 | 高：也包含该主机上的国际酒店页面，不按路径或目的地分流 |
| `flights.ctrip.com` | 桌面官网实际链接 `/online/channel/domestic`、`/international/` 等 | 机票网页入口；默认直连，可选代理 | 高：也包含该主机上的国际航班页面 |
| `trains.ctrip.com` | 桌面官网实际链接 `/`、`/overseasTrains` 等 | 火车票网页入口；默认直连，可选代理 | 高：同主机的境外列车页面也受影响 |
| `vacations.ctrip.com` | 桌面官网实际链接 `/grouptravel`、`/freetravel` 等 | 度假网页入口；默认直连，可选代理 | 高：不按境内/境外旅游产品区分 |

证据仅证明官方页面确实使用或链接相应主机，不代表逐一完成业务功能、持续可用性或服务所有权的独立审计。移动页公开 HTML 还包含故障提示，不能据此声称 App 功能已经实测可用。

## 明确排除

不使用 `ctrip.com`、`c-ctrip.com`、`trip.com`、`tripcdn.com` 等根域后缀。官网确实引用的 `static.tripcdn.com`、`webresource.c-ctrip.com`、图片分片和其他跨旅行品牌资源，本批仍不纳入，避免把共享资源的使用证据当作专属归属。`ct.ctrip.com`、`s.c-ctrip.com`、`hm.baidu.com` 及统计候选不纳入，继续保留既有安全/隐私行为；`my.ctrip.com` 登录、`sec.ctrip.com` 安全验证及未观察的 API 不据猜测扩充。

`www.trip.com`、`english.ctrip.com`、`www.tieyou.com`、`www.tujia.com` 等国际站、关联品牌和其他业务不加入本清单，沿用原路由。它们可能仍被既有规则覆盖；本 PR 不将其改归携程组。

## 路由、限制与复核计划

Privacy/Hijacking、安全例外与两组游戏规则继续在前，携程精确规则放在 Apple、GlobalMedia、GeoIP、ChinaMax 等更宽规则之前；既有 APP 相对顺序、FINAL/MATCH 和所有权限保持不变。

本组只控制七个公开入口主机。静态、API、登录、支付及原生 App 其他请求仍按原规则，手动选择代理可能形成混合出口；不保证搜索、出票、订单、退款、定位、风控或原生 App 全链路覆盖，也不改变价格、账户或地区资格。若切换出口后出现登录或地区识别异常，可先恢复 DIRECT 排查；这只是条件性建议，不是已观察到风控触发的结论。

实施复用现有服务注册、独立策略组和目录生成器，增加真实 `validate_ctrip(root)` / `validate_tree` 门禁与公开 fixture mutation 测试，覆盖精确范围、重复、唯一引用、DIRECT-first select、前置安全、遮蔽、未知 provider、UTF-8 和非目标不变。验证仅为无 IP/进程元数据的离线域名首匹配；DNS、GeoIP、UDP、设备或真实账户行为尚未实测。

## English scope summary

Seven exact public Ctrip entry hosts, evidenced by the official desktop/mobile pages and real navigation links. DIRECT is the default, with an optional manual proxy. This is not full native-app, authentication, booking, payment or shared-CDN coverage. International pages on the same exact hosts are affected too. Security precedence and unrelated brands remain unchanged; no private traffic or credentials were collected.
