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
- [ ] Add repository topics such as `mihomo`, `clash`, `ruleset`, `china`, and `gaming`.

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
- [ ] 添加 `mihomo`、`clash`、`ruleset`、`china`、`gaming` 等仓库主题。
