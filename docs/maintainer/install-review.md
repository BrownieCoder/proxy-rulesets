# 安装系统独立审查与验证记录

日期：2026-09-22。比较基线：`322017d8c41d8a54b586607b55ebd675f02ffa31`。

## Reviewer A：技术

独立 reviewer 最终结论：PASS WITH FOLLOW-UPS；0 BLOCKER、0 MAJOR、0 MINOR。

已修复：发布记录的旧散列不再阻断未来同步；全部候选格式在替换旧资产前构建验证；来源散列使用原始字节；收窄跨内核“无损”与未发布下载承诺。

独立确认原规则、canonical、路由配置、来源锁、许可证均无变化；工作流权限无变化；生成 Privacy 保留全部条目、REJECT、no-resolve 与输出顺序。

## Reviewer B：首次使用者视角

独立 reviewer 结论：PASS WITH FOLLOW-UPS；0 BLOCKER、0 MAJOR。唯一 MINOR 已修复：Markdown 普通链接改称“规则地址”，明确右键/长按复制；真正复制按钮仅在安装页。

已用浏览器检查：ChatGPT 首批卡片与搜索 → Shadowrocket 显示手动状态 → 教程解释不替换节点/主配置 → 三步回退 → Siri 搜索 → Clash Verge 入口和正确 HTML 教程。浏览器拒绝剪贴板时显示可选择的完整 URL。

15 秒是可发现性审阅判断，没有人类首次使用者计时实验；未触发任何客户端 scheme 或真实导入。

## 验证

- `python3 scripts/validate.py`：通过；24 个镜像、4 个本地规则集、28 个服务目录，生成内容一致。
- `python3 scripts/public_check.py`：通过。
- `python3 -m unittest discover -s tests`：20 项通过，含真实同步函数的模拟网络成功/失败路径；失败时全部旧文件字节不变。
- `node --test tests/install_ui.test.cjs`：4 项通过。
- `node tests/browser_install.cjs`：真实本地 Chrome、28 × 5 组合、复制失败、HTML 教程、未发布门槛、六种宽度通过，无页面错误；未启动代理客户端。
- `node --check install/app.js`、`git diff --check`：通过。
- 原路由模拟：Siri 5 个目标与 3136 个非目标样本，安全/游戏顺序通过。实际 DNS、GeoIP、UDP 和设备资格未测试。
- 公开 GET：28 个现有 raw URL 全部 HTTP 200 且与本地字节一致；新模块、拟用 Pages 地址 HTTP 404，明确未发布。记录见 `catalog/online-verification.json`。

## 发布前 FOLLOW-UP

`python3 scripts/public_check.py --release` 尚未通过：旧检查器仅允许 users.noreply.github.com，基线已有 GitHub 合并提交的官方通用 noreply 邮箱（域为 github.com）。独立 reviewer 确认它来自原基线，并非此次新增个人邮箱。本任务不扩大为修改发布扫描器。

其他门槛：另行授权发布、启用 Pages 设置（当前 has_pages=false）、发布后再核验模块及站点 URL，并完成 Shadowrocket 混合域名/IP 规则与客户端唤起真机测试。当前只有本地资产完成，不能宣称线上 READY。

权限变化：NONE。没有网络同步生产规则，没有访问私人配置，也没有 push、merge 或 deploy。
