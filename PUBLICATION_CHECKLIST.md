# Public release checklist / 公开发布检查清单

## Required before the first public push / 首次公开推送前必须完成

- [x] Set the public repository path to `BrownieCoder/proxy-rulesets`.
- [x] Use `BrownieCoder@users.noreply.github.com` for the clean public root commit; do not push the private maintenance history.
- [x] Prepare a clean `public-main` root branch without removed private hostnames or unlicensed material.
- [x] Review the current upstream license and README notices.
- [ ] Run `python3 scripts/validate.py`.
- [ ] Run `python3 scripts/public_check.py --release`.
- [ ] Run `git diff --check`.
- [ ] Test the merged Mihomo configuration with `mihomo -t -f`.
- [ ] Enable GitHub Actions read/write workflow permission.
- [ ] Upload `assets/social-preview.png` under **Settings → Social preview**.
- [ ] Set the repository description to: `Audited Clash/Mihomo rule providers for mainland China gaming: China DIRECT, international safeguards, atomic mirrors, and daily updates.`
- [ ] Add topics: `mihomo`, `clash-meta`, `clash-rules`, `rule-provider`, `ruleset`, `china`, `gaming`, `game-routing`, `proxy`, `direct`, `geosite`, `openclash`.

---

- [x] 公开仓库路径设为 `BrownieCoder/proxy-rulesets`。
- [x] 干净公开根提交使用 `BrownieCoder@users.noreply.github.com`，不推送私人维护历史。
- [x] 准备不含已删除私人主机名或无许可证材料的 `public-main` 干净根分支。
- [x] 复核上游当前许可证与 README 声明。
- [ ] 运行 `python3 scripts/validate.py`。
- [ ] 运行 `python3 scripts/public_check.py --release`。
- [ ] 运行 `git diff --check`。
- [ ] 使用 `mihomo -t -f` 检查合并后的配置。
- [ ] 启用 GitHub Actions 的读写权限。
- [ ] 在 **Settings → Social preview** 上传 `assets/social-preview.png`。
- [ ] 仓库描述设为：`Audited Clash/Mihomo rule providers for mainland China gaming: China DIRECT, international safeguards, atomic mirrors, and daily updates.`
- [ ] 添加 topics：`mihomo`、`clash-meta`、`clash-rules`、`rule-provider`、`ruleset`、`china`、`gaming`、`game-routing`、`proxy`、`direct`、`geosite`、`openclash`。
