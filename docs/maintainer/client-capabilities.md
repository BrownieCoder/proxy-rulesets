# 客户端安装能力核验

核验日期：2026-09-22。本页供维护者审查安装入口的真实性，不代表所有客户端版本、系统和浏览器都已经实测。

本次核验范围是公开文档和公开源码。没有执行真实客户端导入，也没有验证真实代理流量。开源客户端行为以本文固定的已发布版本为准；Shadowrocket 是闭源应用，模块行为使用明确标注的社区手册作为依据。

## 能力与本仓库入口

| 客户端与核验版本 | 客户端支持的导入 | 对已有配置的影响 | 本仓库适合提供的入口 |
| --- | --- | --- | --- |
| Shadowrocket；社区手册固定版本 | 通过 URL 安装模块 | 模块规则优先于主配置；仅规则模块不携带节点和主配置设置 | 仅对能够保留原策略与优先级的规则生成模块；其他服务显示手动配置 |
| ClashX.Meta v1.4.45 | 通过 URL 导入完整配置 | 确认后导入并切换；同名远程配置可能被替换 | 复制规则 URL、手动配置说明；不能称为一键添加当前规则 |
| Clash Verge Rev v2.5.5 | 通过 URL 导入完整配置 | 新增配置；已有当前配置时不自动切换，没有当前配置时会选中并尝试加载 | 复制规则 URL、已有订阅的扩展配置与规则编辑教程 |
| Clash Party v2.0.3（原 Mihomo Party） | 通过 URL 导入完整配置 | 新增配置；已有当前配置时不自动切换，没有当前配置时会切换 | 复制规则 URL、已有配置的覆写教程 |
| 其他 Mihomo 客户端 | 取决于具体应用 | 内核名称不能证明应用的导入或合并行为 | 复制规则 URL、通用手动配置说明 |

**客户端支持完整配置的一键导入，不等于本仓库的单个规则文件可以一键装入当前配置。** 不得把只含 `payload` 的规则文件放进完整配置导入链接；不得为了使其通过客户端检查而添加假节点或改变兜底策略。

## 来源层级

- 官方产品资料：开发者网站、官方 App Store 页面。
- 官方文档：客户端项目维护的文档站或 README。
- 官方源码：对应已发布版本的固定 commit；本文据此追踪导入、新建、切换和覆盖行为。
- 社区原始手册：LOWERTOP 的 Shadowrocket 使用手册补完计划，不能称为官方规范或真机验证。
- 本仓库推断：根据上述行为判断规则格式是否适合无损转换、是否应开放安装按钮。推断不得改写为客户端官方保证。

安装按钮只能指向已经生成、经过检查并已公开可访问的资产。文档或源码核验不能代替远程文件的 GET/HEAD 检查，也不能代替浏览器到应用的实际唤起测试。

## Shadowrocket

### 证据与 scheme

[App Store 产品页](https://apps.apple.com/us/app/shadowrocket/id932747118)和[开发者网站](https://shadowlaunch.com/)可核验产品身份及规则文件功能。本次未找到开发者公开的模块 URL Scheme 规范或可供审计的客户端源码。

模块入口来自 [LOWERTOP 社区手册的固定版本](https://github.com/LOWERTOP/Shadowrocket/blob/6336a2e010660b5ef70cb2a0d77e5f5988dc1501/README.md#L1844)：

```text
shadowrocket://install?module=<编码后的模块 HTTPS URL>
```

生成器应将完整模块 URL 当作一个查询参数值进行 percent encoding，并验证解码后的值与原始 URL 完全一致。不能对整个 scheme 一起编码，也不能让远程 URL 中的 `&`、`#` 等字符变成外层参数或片段。手册给出了参数形式，但没有严格规定编码细节；本项目的编码及往返测试属于实现检查，不是客户端真机验证。

### 模块行为与转换边界

[模块说明](https://github.com/LOWERTOP/Shadowrocket/blob/6336a2e010660b5ef70cb2a0d77e5f5988dc1501/README.md#L1149)说明模块可只包含配置的部分内容，模块之间可以排序。[规则优先级说明](https://github.com/LOWERTOP/Shadowrocket/blob/6336a2e010660b5ef70cb2a0d77e5f5988dc1501/README.md#L680)明确模块规则优先于主配置，并描述域名类与 IP 类规则的优先级差异。

本次没有找到让模块排在主配置之后、或插入主配置指定位置的可靠依据。因此，把某个服务单独变成模块，可能使它先于主配置中的屏蔽规则或精确覆盖规则生效。仅仅保证规则文本相同，不能证明最终路由相同。

[规则类型列表](https://github.com/LOWERTOP/Shadowrocket/blob/6336a2e010660b5ef70cb2a0d77e5f5988dc1501/README.md#L690)包含 DOMAIN、DOMAIN-SUFFIX、DOMAIN-KEYWORD、IP-CIDR 和 IP-ASN 等类型。PROCESS-NAME 未在本次核验材料中得到兼容性证明；这意味着不能按已验证类型生成，不意味着已经证明所有平台和版本绝对不支持它。

[策略说明](https://github.com/LOWERTOP/Shadowrocket/blob/6336a2e010660b5ef70cb2a0d77e5f5988dc1501/README.md#L759)区分 PROXY、DIRECT、REJECT 及自定义分组。本次没有找到未定义策略组名称的可靠安全回退保证。

本仓库据此采用以下边界：

- 不把允许用户选择 DIRECT 的服务策略组改为固定 PROXY。
- 不引用用户配置中未必存在的策略组名称来伪装开箱即用。
- 不把依赖游戏顺序、精确域名覆盖或更早屏蔽规则的服务自动转换为独立模块。
- Privacy 使用固定 REJECT 且位于现有规则的屏蔽优先位置，只有其规则类型和生成一致性检查通过时，才适合提供独立模块。

仅规则模块可以说明“不替换节点和主配置”，但仍应说明它会改变命中域名的处理方式。推荐用户文案：

> 仅添加本页列出的屏蔽规则，不替换节点和主配置。模块规则优先于主配置，可能覆盖主配置对同一域名的放行规则。

这不构成对所有第三方主配置、其他模块或客户端编译行为的无条件无损保证。不要写“完全不影响其他流量”。

### 系统与回退

App Store 列出 iPhone、iPad、Mac 和 Apple TV 平台；本次未逐平台验证 URL 唤起。入口首先面向已安装 Shadowrocket 的用户，浏览器可能要求确认打开应用。

模块自动打开失败时，最多三步：

1. 复制模块 URL。
2. 打开 Shadowrocket 的“配置 → 模块 → ＋”。
3. 粘贴、下载并启用；规则模块需要在配置路由模式下使用。

没有可用模块的服务应显示“手动配置”，不能将 Mihomo YAML 地址当作已验证的 Shadowrocket 模块地址。

## ClashX.Meta

### 固定版本与参数

核验版本：[v1.4.45](https://github.com/MetaCubeX/ClashX.Meta/releases/tag/v1.4.45)，commit `5370f56beebd2f92fb7d8ef8e58892ece0b76c1c`。不要用旧默认分支的代码代替这个已发布版本。

[官方 README](https://github.com/MetaCubeX/ClashX.Meta/blob/5370f56beebd2f92fb7d8ef8e58892ece0b76c1c/README.md#L61)给出完整配置导入语法，并明确提示 scheme 可能无法工作：

```text
clash://install-config?url=<编码后的完整配置 URL>&name=<编码后的名称>
```

`url` 必需，`name` 可选。应分别编码每个参数值。[解析入口](https://github.com/MetaCubeX/ClashX.Meta/blob/5370f56beebd2f92fb7d8ef8e58892ece0b76c1c/ClashX/AppDelegate.swift#L789)使用 URLComponents 读取这两个参数。

### 导入、切换与覆盖

[导入窗口处理](https://github.com/MetaCubeX/ClashX.Meta/blob/5370f56beebd2f92fb7d8ef8e58892ece0b76c1c/ClashX/ViewControllers/RemoteConfigViewController.swift#L84)先要求用户确认；scheme 入口允许修改同名远程配置，因此重名时可能替换原有地址和内容。

[导入完成处理](https://github.com/MetaCubeX/ClashX.Meta/blob/5370f56beebd2f92fb7d8ef8e58892ece0b76c1c/ClashX/ViewControllers/RemoteConfigViewController.swift#L148)会加载新导入的配置；[配置加载器](https://github.com/MetaCubeX/ClashX.Meta/blob/5370f56beebd2f92fb7d8ef8e58892ece0b76c1c/ClashX/General/Managers/ConfigReloadManager.swift#L55)在成功时更新当前配置选择。[远程配置写入](https://github.com/MetaCubeX/ClashX.Meta/blob/5370f56beebd2f92fb7d8ef8e58892ece0b76c1c/ClashX/General/Managers/RemoteConfigManager.swift#L203)会替换目标位置已有文件。

因此准确表述是：导入完整配置并可能立即切换；同名远程配置可能被替换，不会自动合并到当前配置。不得写“只新增、绝不影响当前配置”。

当前 [ConfigOverride](https://github.com/MetaCubeX/ClashX.Meta/blob/5370f56beebd2f92fb7d8ef8e58892ece0b76c1c/ClashX/General/Managers/ConfigOverride.swift#L75)处理应用运行设置，不是独立规则 URL 的安装接口。

### 系统与回退

ClashX.Meta 面向 macOS。系统中多个应用可能注册同一个 `clash` scheme；本次没有实测浏览器唤起。

本仓库的规则 URL 不应粘贴进“远程配置”当作完整配置。回退路径是：复制规则 URL → 打开当前配置的本地副本 → 按本仓库手动教程接入规则并保持原顺序。

若未来提供完整示例配置，必须明确节点由用户自行配置、导入后的切换影响及重名风险，不能把示例称为已经给当前配置加好规则。

## Clash Verge Rev

### 固定版本与编码要求

核验版本：[v2.5.5](https://github.com/clash-verge-rev/clash-verge-rev/releases/tag/v2.5.5)，commit `22e3f1ac8aefe4102ae2eb646a11a1ec614e8576`。

[官方文档](https://www.clashverge.dev/guide/url_schemes.html)支持完整配置 URL 导入，要求把远程 URL 的全部查询参数一起编码。[应用注册](https://github.com/clash-verge-rev/clash-verge-rev/blob/22e3f1ac8aefe4102ae2eb646a11a1ec614e8576/src-tauri/tauri.conf.json#L44)同时包含 `clash` 和 `clash-verge`。

```text
clash-verge://install-config?name=<编码后的名称>&url=<编码后的完整配置 URL>
```

**该版本的 `url` 参数必须放在最后。** [解析实现](https://github.com/clash-verge-rev/clash-verge-rev/blob/22e3f1ac8aefe4102ae2eb646a11a1ec614e8576/src-tauri/src/utils/resolve/scheme.rs#L41)从 `url=` 后一直读取到查询字符串末尾；如果把 `&name=` 放在后面，它可能成为远程 URL 的一部分。不需要名称时只生成 `url` 参数即可。

### 配置行为与替代入口

[导入处理](https://github.com/clash-verge-rev/clash-verge-rev/blob/22e3f1ac8aefe4102ae2eb646a11a1ec614e8576/src-tauri/src/utils/resolve/scheme.rs#L82)和[配置追加实现](https://github.com/clash-verge-rev/clash-verge-rev/blob/22e3f1ac8aefe4102ae2eb646a11a1ec614e8576/src-tauri/src/config/profiles.rs#L180)表明：新增一个配置，已有当前配置时不自动切换；当前配置为空时选中新配置并尝试加载。

[内容验证](https://github.com/clash-verge-rev/clash-verge-rev/blob/22e3f1ac8aefe4102ae2eb646a11a1ec614e8576/src-tauri/src/config/prfitem.rs#L360)要求存在 `proxies` 或 `proxy-providers`。只有规则 `payload` 的文件不是这个入口接受的完整配置。

对于已有节点的用户，更合适的是[官方扩展配置与规则编辑入口](https://www.clashverge.dev/guide/extend.html)。扩展可以修改已有配置；但是否放在规则前面、替换数组或补充对象，必须按客户端实际语义处理。普通安装 scheme 不会替用户完成这些操作。

### 系统与回退

[官方订阅教程](https://www.clashverge.dev/guide/profile.html)说明 macOS 从 2.0 起支持 scheme；Windows 可能受其他 Clash 软件的协议注册影响。[Linux 注册源码](https://github.com/clash-verge-rev/clash-verge-rev/blob/22e3f1ac8aefe4102ae2eb646a11a1ec614e8576/src-tauri/src/lib.rs#L80)包含运行时协议注册。以上不能证明每一种便携版、发行包装和浏览器都可成功唤起。

本仓库推荐：复制规则 URL → 打开已有订阅的扩展配置与规则编辑入口 → 按教程接入并检查最终顺序。不要把规则 URL 粘到订阅导入框。

对于真正的完整配置 URL，scheme 失败时可以复制 URL → 打开“订阅” → 粘贴导入；这会新增配置，不会合并规则。

## Mihomo Party / Clash Party

### 稳定版结论

核验版本：[Clash Party v2.0.3](https://github.com/mihomo-party-org/clash-party/releases/tag/v2.0.3)，commit `8cf3515a20c0d73ceb077a9ab831e791fa4b8e6d`。Mihomo Party 是用户熟悉的旧名称；界面和文档可同时注明当前名称 Clash Party。

[官方 URL Scheme 文档](https://clashparty.org/docs/guide/urlscheme)给出：

```text
mihomo://install-config?url=<编码后的完整配置 URL>&name=<编码后的名称>
```

`url` 必需，`name` 可选。分别编码两个参数值；[解析源码](https://github.com/mihomo-party-org/clash-party/blob/8cf3515a20c0d73ceb077a9ab831e791fa4b8e6d/src/main/deeplink.ts#L18)通过 URLSearchParams 读取。[打包配置](https://github.com/mihomo-party-org/clash-party/blob/8cf3515a20c0d73ceb077a9ab831e791fa4b8e6d/electron-builder.yml#L23)也注册 `clash`，但本客户端入口优先使用文档明确给出的 `mihomo`。

[新增配置实现](https://github.com/mihomo-party-org/clash-party/blob/8cf3515a20c0d73ceb077a9ab831e791fa4b8e6d/src/main/config/profile.ts#L201)表明：已有当前配置时不自动切换；没有当前配置时会切换到新配置。[内容检查](https://github.com/mihomo-party-org/clash-party/blob/8cf3515a20c0d73ceb077a9ab831e791fa4b8e6d/src/main/config/profile.ts#L463)要求 `proxies` 或 `proxy-providers`，不能直接导入纯规则文件。

[官方 YAML 覆写说明](https://clashparty.org/docs/guide/override/yaml)区分数组替换、前插和追加：普通 `rules` 会替换规则数组，`+rules` 前插，`rules+` 追加。前插可能越过既有屏蔽规则，追加可能位于 MATCH 之后而不生效；不能将任意覆写片段称为安全自动合并。

### 系统与回退

官方打包配置覆盖 Windows、macOS 和 Linux，并为 Linux 配置 scheme handler。实际唤起仍取决于应用安装方式、浏览器和系统协议关联。

本仓库推荐：复制规则 URL → 打开已有配置的覆写入口 → 按教程接入并检查最终顺序。完整配置导入失败时则使用客户端配置页面的远程配置导入入口，不要混淆两种 URL。

### 后续开发版本提醒

本节不改变上述 v2.0.3 的结论。核验时，尚未包含在该稳定版中的 `smart_core` 开发提交 `e36747bcbb131110dc254061523be26b7453762c` 已增加简易模式分支：[新增配置分支](https://github.com/mihomo-party-org/clash-party/blob/e36747bcbb131110dc254061523be26b7453762c/src/main/config/profile.ts#L223)会调用[简易模式订阅配置逻辑](https://github.com/mihomo-party-org/clash-party/blob/e36747bcbb131110dc254061523be26b7453762c/src/main/simple/service.ts#L567)，后者更新草稿及已发布状态。

因此不能把稳定版“已有当前配置时不自动切换”的结论扩展成所有未来版本“导入绝不会影响运行状态”的保证。升级客户端支持范围时需要重新追踪该分支。

## 验证与维护要求

本次已完成文档和固定源码读取，未进行真实设备或浏览器到客户端的导入测试。发布和后续维护仍须分别检查：

- 规则与模块来自同一来源，条目、策略、顺序和生成哈希符合生成契约。
- module 中没有节点、订阅、MITM、rewrite、script、DNS 或 FINAL。
- 安装链接的参数编码可往返还原，按钮和复制 URL 指向同一个实际资产。
- 已发布 raw URL 可访问；未发布文件不可标为在线可用。
- README、安装中心和 fallback 对“模块”“规则文件”“完整配置”的称呼一致。
- 更换客户端支持版本后重新检查导入、重名、切换、合并及跨平台注册行为。

本页只记录公开客户端能力，不需要读取用户节点、订阅或私有配置。权限变化：`NONE`。
