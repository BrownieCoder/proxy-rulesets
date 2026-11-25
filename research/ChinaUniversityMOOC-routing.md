# 中国大学 MOOC公开入口分流依据

基线：`c594b80a278cc48e4e363747a9627d8b2bae29be`。新增 `DOMAIN,www.icourse163.org`，对应 `🎓 中国大学 MOOC` 策略组，默认直连（DIRECT），也可手动选择节点或 Final。

## 官方依据

- [中国大学 MOOC 官网](https://www.icourse163.org/)：公开页面显示网易与高等教育出版社的中国大学 MOOC 品牌；本次未同意隐私弹窗或验证课程功能。
- [中国区 App Store](https://apps.apple.com/cn/app/id977883304)：中国大学 MOOC（慕课）的开发者网站链接指向该主机，隐私链接所用的 `corp.163.com` 不另纳入。

证据支持公开入口的主机归属，不证明原生客户端调用范围。未安装客户端、登录或采集流量。

## 作用与边界

同主机所有路径均随组；网易共享域、图片资源、独立账号和播放器接口不另纳入。未验证原生 App、课程播放、登录、作业或考试链路。 规则按主机匹配，不按 URL 路径或发起进程匹配；不同主机可能走不同出口。

基线离线域名模型的原首匹配为 `ChinaMax → 🇨🇳 China-Global`。新增项位于安全、游戏和既有 App 规则之后、SiriAI 与通用规则之前，末尾 MATCH 不变。未实测 DNS、GeoIP、UDP 或原生 App 行为。

对照：`icourse163.org`、`m.icourse163.org`、`corp.163.com`、`study.163.com`、`higher.smartedu.cn`、`mooc-image.nosdn.127.net`、`dict.youdao.com`、`music.163.com`、`example.org` 保持原策略；另核对目标的子域、相似标签与伪装后缀。

## English scope

Only `www.icourse163.org` gets a dedicated DIRECT-first selector for China University MOOC. All paths on that hostname follow the selector; other hosts keep their existing routes. This is not full native-app coverage; live network and client behavior were not tested.
