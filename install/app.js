"use strict";

(() => {
  const catalog = window.INSTALL_CATALOG;
  const byId = (id) => document.getElementById(id);
  if (!catalog || !Array.isArray(catalog.services) || !catalog.services.length || !Array.isArray(catalog.clients) || !catalog.clients.length) {
    byId("catalog-error").hidden = false;
    return;
  }

  const aliases = {
    openai: "chatgpt chat gpt GPT 聊天 人工智能",
    siriai: "siri apple intelligence 苹果智能 苹果 智能 语音 听写",
    "siri-ai": "siri apple intelligence 苹果智能 苹果 智能 语音 听写",
    chinagaming: "国内游戏 国服 中国大陆游戏 腾讯 网易 米哈游 游戏",
    internationalgaming: "国际游戏 国际服 海外游戏 游戏",
    steamcn: "蒸汽平台 国服 蒸汽 游戏",
    steam: "steam 游戏",
    claude: "anthropic AI 人工智能",
    gemini: "google bard AI 人工智能",
    twitter: "x 推特 社交",
    disney: "disney+ 迪士尼 影视",
    netflix: "奈飞 网飞 影视",
    bilibili: "哔哩哔哩 b站 视频",
    youtube: "油管 视频",
    telegram: "电报 社交",
    microsoft: "微软",
    apple: "苹果",
    google: "谷歌"
  };
  const services = catalog.services;
  const clients = catalog.clients;
  const normalize = (text) => String(text || "").toLocaleLowerCase().replace(/[\s_-]+/g, "");
  const params = new URLSearchParams(window.location.search);
  let service = services.find((item) => item.id === params.get("service")) || services.find((item) => normalize(item.id) === "siriai") || services.find((item) => normalize(item.id) === "openai") || services[0];
  let client = clients.find((item) => item.id === params.get("client")) || null;
  let category = "全部";
  let toastTimeout;

  const make = (tag, className, text) => {
    const element = document.createElement(tag);
    if (className) element.className = className;
    if (text !== undefined) element.textContent = text;
    return element;
  };

  function link(text, href, className) {
    const anchor = make("a", className, text);
    // Catalog links are public HTTP(S) URLs or repository-relative documentation.
    const parsed = new URL(href, window.location.href);
    if (!["https:", "http:", "file:"].includes(parsed.protocol)) return null;
    anchor.href = parsed.href;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
    return anchor;
  }

  function appendLink(parent, text, href, className) {
    if (!href) return;
    const anchor = link(text, href, className);
    if (anchor) parent.append(anchor);
  }

  function updateLocation() {
    const next = new URL(window.location.href);
    next.searchParams.set("service", service.id);
    if (client) next.searchParams.set("client", client.id);
    else next.searchParams.delete("client");
    // Some browsers restrict History API updates on file://. Selection still works.
    try { window.history.replaceState(null, "", next.href); } catch (error) {
      if (error.name !== "SecurityError") throw error;
    }
  }

  function showToast(message) {
    window.clearTimeout(toastTimeout);
    byId("toast").textContent = message;
    byId("toast").hidden = false;
    toastTimeout = window.setTimeout(() => { byId("toast").hidden = true; }, 4500);
  }

  async function copyUrl(url) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(url);
        showToast("链接已复制，请按下方步骤添加规则。");
        return;
      } catch (error) {
        // A visible, selectable URL is the fallback when clipboard access is denied.
      }
    }
    byId("copy-fallback").hidden = false;
    byId("copy-url").value = url;
    byId("copy-url").focus();
    byId("copy-url").select();
    showToast("请复制已选中的完整链接。");
  }

  function copyButton(text, url, className) {
    const button = make("button", className, text);
    button.type = "button";
    button.addEventListener("click", () => copyUrl(url));
    return button;
  }

  function serviceIcon(item) {
    const id = normalize(item.id);
    if (id.includes("siri")) return "S";
    if (id.includes("openai")) return "AI";
    if (/gaming|steam/.test(id)) return "+";
    if (id.includes("claude")) return "✳";
    if (id.includes("gemini")) return "✦";
    return item.name.slice(0, 1).toUpperCase();
  }

  function renderServices() {
    const query = normalize(byId("service-search").value);
    const visible = services.filter((item) => {
      const extra = aliases[normalize(item.id)] || aliases[normalize(item.provider)] || "";
      const haystack = normalize([item.id, item.name, item.category, item.description, extra].join(" "));
      return (category === "全部" || item.category === category) && (!query || haystack.includes(query));
    });
    const list = byId("service-list");
    list.replaceChildren();
    for (const item of visible) {
      const button = make("button", "service-card");
      button.type = "button";
      button.setAttribute("aria-pressed", String(item.id === service.id));
      button.dataset.service = item.id;
      button.dataset.categoryTone = /游戏|gaming/i.test(item.category) ? "game" : /影音|媒体|视频|media/i.test(item.category) ? "media" : "other";
      const icon = make("span", "service-icon", serviceIcon(item));
      icon.setAttribute("aria-hidden", "true");
      const copy = make("span", "service-card-copy");
      copy.append(make("span", "service-card-title", item.name), make("span", "service-card-description", item.description));
      button.append(icon, copy);
      button.addEventListener("click", () => {
        service = item;
        list.querySelectorAll(".service-card").forEach((card) => card.setAttribute("aria-pressed", String(card.dataset.service === item.id)));
        renderSelected();
        updateLocation();
        byId("search-result").textContent = `已选择 ${item.name}。${client ? "安装方式已更新。" : "下一步请选择客户端。"}`;
      });
      list.append(button);
    }
    byId("service-count").textContent = `${visible.length} / ${services.length} 项服务`;
    byId("search-result").textContent = `找到 ${visible.length} 项服务`;
    byId("empty-state").hidden = visible.length > 0;
    list.hidden = visible.length === 0;
  }

  function renderCategories() {
    const categories = ["全部", ...new Set(services.map((item) => item.category))];
    const filters = byId("category-filters");
    categories.forEach((name) => {
      const button = make("button", "filter-button", name);
      button.type = "button";
      button.setAttribute("aria-pressed", String(name === category));
      button.addEventListener("click", () => {
        category = name;
        filters.querySelectorAll("button").forEach((item) => item.setAttribute("aria-pressed", String(item.textContent === category)));
        renderServices();
      });
      filters.append(button);
    });
  }

  function renderClients() {
    const list = byId("client-list");
    for (const item of clients) {
      const button = make("button", "client-button");
      button.type = "button";
      button.setAttribute("aria-pressed", String(Boolean(client && item.id === client.id)));
      button.dataset.client = item.id;
      button.append(make("span", "", item.name), make("small", "", item.platform));
      button.addEventListener("click", () => {
        client = item;
        list.querySelectorAll("button").forEach((node) => node.setAttribute("aria-pressed", String(node.dataset.client === item.id)));
        renderSelected();
        updateLocation();
        byId("install-section").scrollIntoView({ block: "nearest" });
        byId("search-result").textContent = `已选择 ${item.name}，接入方式已更新。`;
      });
      list.append(button);
    }
  }

  function renderSelected() {
    byId("selected-name").textContent = service.name;
    byId("selected-category").textContent = service.category;
    byId("selected-description").textContent = service.description;
    byId("selected-policy").textContent = `建议去向：${service.policyLabel || service.policy}`;
    byId("selected-count").textContent = Number.isInteger(service.ruleCount) ? `${service.ruleCount} 条规则` : "";
    byId("service-warning").textContent = service.warning || "";
    byId("service-warning").hidden = !service.warning;
    byId("install-section").hidden = !client;
    byId("choose-client-note").hidden = Boolean(client);
    byId("copy-fallback").hidden = true;
    byId("copy-url").value = "";
    if (!client) return;

    byId("client-summary").textContent = client.summary;
    const moduleClient = client.mode === "module";
    const readyModule = moduleClient && service.module && service.module.published === true;
    const hasScheme = readyModule && typeof service.module.schemeUrl === "string" && service.module.schemeUrl.startsWith("shadowrocket://");
    const actions = byId("install-actions");
    actions.replaceChildren();
    byId("install-badge").dataset.ready = String(Boolean(readyModule));
    byId("fallback-details").open = true;

    if (readyModule) {
      byId("install-badge").textContent = "模块已发布";
      byId("install-explanation").textContent = "打开客户端添加此规则模块。导入后检查模块是否启用，并确认实际命中的规则与出口。";
      byId("format-warning").textContent = "这是规则模块，不包含节点。它会影响匹配流量的去向；请先备份当前配置，并阅读本服务的限制。";
      if (hasScheme) {
        const importLink = make("a", "action action-primary", `在 ${client.name} 中导入 ↗`);
        importLink.href = service.module.schemeUrl;
        importLink.addEventListener("click", () => {
          showToast("已尝试打开客户端；若没有响应，请复制模块链接并按三步操作。");
        });
        actions.append(importLink);
      }
      if (service.module.rawUrl) actions.append(copyButton("复制模块链接", service.module.rawUrl, `action ${hasScheme ? "action-secondary" : "action-primary"}`));
      byId("fallback-title").textContent = "没有打开客户端？按这三步添加";
    } else if (moduleClient) {
      const unpublished = Boolean(service.module);
      byId("install-badge").textContent = unpublished ? "模块尚未发布" : "需手动配置";
      byId("install-explanation").textContent = unpublished
        ? "此服务的客户端模块尚未公开发布，暂时不能一键导入。请先查看教程；发布前不要使用模块地址。"
        : `此服务还没有可直接导入的客户端模块。${service.moduleReason || "请查看教程，按规则内容手动配置，并核对流量去向与规则顺序。"}`;
      byId("format-warning").textContent = "下方原始规则是 Mihomo YAML 格式，不能直接导入 Shadowrocket，也不能粘贴到订阅或模块入口。";
      appendLink(actions, "查看手动配置教程 ↗", client.guideUrl || service.guideUrl, "action action-primary");
      byId("fallback-title").textContent = "手动配置前，先完成这三步";
    } else {
      byId("install-badge").textContent = "规则集接入";
      byId("install-explanation").textContent = "复制此服务的规则集链接，再按教程将它加入当前配置，并关联你已有的策略组。";
      byId("format-warning").textContent = "这是 Mihomo rule-provider 规则集，不是完整配置或订阅。请勿粘贴到“添加订阅”入口；复制链接本身不会启用分流。";
      if (service.rawUrl) actions.append(copyButton("复制规则集链接", service.rawUrl, "action action-primary"));
      appendLink(actions, "查看教程 ↗", client.guideUrl || service.guideUrl, "action action-secondary");
      byId("fallback-title").textContent = "复制之后，按这三步完成";
    }

    const fallback = byId("fallback-steps");
    fallback.replaceChildren();
    let steps = client.fallback;
    if (moduleClient && !readyModule) {
      steps = [
        "备份当前配置，先打开本客户端的手动配置教程，确认规则语法与添加位置。",
        "只把原始 Mihomo 规则作为对照材料；按教程转换兼容规则，并使用你已有的策略。不要直接导入 YAML。",
        "核对安全、游戏及宽泛规则的先后顺序，再检查连接记录中的命中规则与实际出口。"
      ];
    }
    (Array.isArray(steps) ? steps : []).forEach((step) => fallback.append(make("li", "", step)));

    const resources = byId("resource-links");
    resources.replaceChildren();
    appendLink(resources, moduleClient && !readyModule ? "原始 Mihomo 规则（只读） ↗" : "查看原始规则 ↗", readyModule ? service.module.rawUrl : service.rawUrl);
    appendLink(resources, "来源与说明 ↗", service.sourceUrl);
    if (service.guideUrl && service.guideUrl !== client.guideUrl) appendLink(resources, "服务说明 ↗", service.guideUrl);
  }

  const repositoryLink = byId("repository-link");
  if (typeof catalog.repository === "string" && /^[\w.-]+\/[\w.-]+$/.test(catalog.repository)) repositoryLink.href = `https://github.com/${catalog.repository}`;
  if (!catalog.siteUrl) {
    byId("publication-note").textContent = "本地预览 · 安装页尚未公开上线。已有公开规则可按教程使用；未发布模块不会提供一键导入。";
    byId("publication-note").hidden = false;
  }
  byId("installer").hidden = false;
  renderCategories();
  renderServices();
  renderClients();
  renderSelected();
  byId("service-search").addEventListener("input", renderServices);
  byId("clear-search").addEventListener("click", () => {
    category = "全部";
    byId("service-search").value = "";
    byId("category-filters").querySelectorAll("button").forEach((item) => item.setAttribute("aria-pressed", String(item.textContent === category)));
    renderServices();
    byId("service-search").focus();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && !event.metaKey && !event.ctrlKey && !event.altKey && !event.target.matches("input, textarea, [contenteditable]")) {
      event.preventDefault();
      byId("service-search").focus();
    }
  });
})();
