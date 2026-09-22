# 将规则接入现有 Clash / Mihomo 配置

[返回服务目录](../../README.md#选择服务)

**规则地址不是节点订阅，也不是完整配置。不要粘贴到“导入订阅 / 远程配置”入口。** 下面会编辑或覆写当前配置，请先备份。规则文件不包含节点；你仍需使用自己已有的策略和节点。

最短路径：复制服务页规则地址 → 按下方客户端入口接入 → 选策略并检查顺序后启用。

## ClashX.Meta

在菜单的配置目录中，复制当前配置为一个本地副本并编辑。将下方规则集合添加到 `rule-providers`，把引用加入 `rules` 的适当位置，再从配置菜单选择这个本地副本。不要直接修改会被远程更新覆盖的下载文件。

`clash://install-config` 导入的是完整远程配置：确认后会切换，同名配置可能被替换，**不会自动把规则合并到当前配置**。本仓库不把 provider 当作 profile 导入。

## Clash Verge Rev

使用当前订阅的扩展配置入口添加规则集合，并通过规则编辑/脚本检查引用的插入位置。入口和配置合并方法见[官方扩展教程](https://www.clashverge.dev/guide/extend.html)。不要直接把完整 `rules` 示例覆盖到订阅扩展里，也不要盲目前插所有规则；保存后查看生成的配置再启用。

完整配置的 scheme 在 v2.5.5 中通常新增一份配置，已有当前配置时不自动切换，没有当前配置时可能启用。Windows 协议注册冲突、macOS 版本和 Linux 包装方式都可能影响浏览器唤起。

## Clash Party

原 Mihomo Party，v2.0.3 可以将 YAML 覆写绑定到目标配置，见[官方覆写规则](https://clashparty.org/docs/guide/override/yaml)。普通 `rules` 会替换整个数组，`+rules` 前插，`rules+` 追加。**前插可能越过安全规则，追加到 MATCH 后则不会生效**；必须检查生成结果，调整到本仓库要求的位置。

v2.0.3 的完整配置导入通常新增，有当前配置时不自动切换；无当前配置时会选择新配置。后续开发版本有简易模式分支，不能把稳定版行为泛化到所有版本。不要把单个规则文件当订阅导入。

## 添加一个服务：以 ChatGPT 为例

这两段是编辑参考，**不是可以独立导入的完整配置**。如果配置已存在同名顶层字段，请合并字段内容，不要重复添加同名字段。

在现有 `rule-providers` 内增加：

```yaml
  OpenAI:
    type: http
    behavior: classical
    url: https://raw.githubusercontent.com/BrownieCoder/proxy-rulesets/main/ruleset/OpenAI_No_Resolve.yaml
    path: ./ruleset-cache/OpenAI_No_Resolve.yaml
    interval: 86400
```

然后在现有 `rules` 内适当位置加入（将 `🤖 OpenAI` 换成你已有的真实策略组名称）：

```yaml
  - RULE-SET,OpenAI,🤖 OpenAI
```

此行必须在安全拦截、游戏和原有更高优先级服务之后，在更宽的通用/中国规则及最终 MATCH 之前。原方案中支付、社交和媒体也在 OpenAI 之前；完整顺序以[有序模板](../../config/rules.yaml)为准。本例不是一条可盲目前插的覆盖规则。

其他服务的文件和原目标策略可在对应服务页找到；完整集合见[远程模板](../../config/rule-providers.remote.yaml)。Claude 还包含有序模板中的补充规则，国际游戏还依赖 `fastcdn.hoyoverse.com` 的精确直连例外，不能只复制单个 provider 宣称完整复现。

检查：客户端的配置检查，或在本机运行 `mihomo -t -f your-config.yaml`。再看实际连接命中；YAML 通过不代表 DNS、GeoIP、UDP 和所有出口都已验证。

如果不熟悉 YAML，保留现有可用配置并请熟悉该客户端的人协助；本仓库不会把需要手动接入的步骤伪装成已完成安装。
