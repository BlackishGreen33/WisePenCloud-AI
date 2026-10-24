# 布局与页内导航组件

内嵌页只呈现用户要求的内容，不复制 WisePen 主导航、全局侧栏、顶部产品栏或用户账号区。

## 默认内容页

```html
<main class="main">
  <header class="page-header">
    <div class="stack gap-xs">
      <h1 class="page-title">页面标题</h1>
      <p class="meta">一句说明</p>
    </div>
    <div class="page-actions">
      <button class="btn" type="button">次要操作</button>
      <button class="btn btn-primary" type="button">主操作</button>
    </div>
  </header>
  <div class="page-body stack gap-md">
    <!-- 用户要求的内容 -->
  </div>
</main>
```

没有页面级操作时省略 `.page-actions`。一个操作区域至多放一个 `.btn-primary`。

## 居中单卡

用于操作说明、结果确认、教学提示等短内容，不用于登录、注册或账号流程。

```html
<main class="stage">
  <section class="card card-narrow stack gap-md">
    <h1 class="title-2">操作说明</h1>
    <p class="body">在这里说明当前内容。</p>
  </section>
</main>
```

## 通用布局 class

- `.stack`：纵向 Flex；配合 `.gap-3xs`、`.gap-2xs`、`.gap-xs`、`.gap-sm`、`.gap-md`、`.gap-lg`。
- `.row`：普通横向排列。
- `.cluster`：一组同类横向内容。
- `.spacer`：占用剩余横向空间。
- `.ellipsis`：单行截断。
- `.muted`：次要文字颜色。
- `.sr-only`：只供辅助技术读取的文字。

页面特有的多列内容可增加自己的 Grid class；间距和视觉值必须使用公开变量，并在窄窗口回落为单列。

## 标题和正文

```html
<h1 class="page-title">页面标题</h1>
<h2 class="section-title">内容分区</h2>
<h2 class="title-2">重点标题</h2>
<h3 class="title-3">卡片标题</h3>
<p class="body">正文内容</p>
<p class="meta">辅助说明</p>
```

不要只为改变外观跳过标题层级；语义层级与视觉 class 应同时合理。

## 分段页签

用于少量互斥视图。按钮必须通过脚本同步 `is-selected`、`aria-selected` 和对应面板的 `hidden`。

```html
<div class="tabs" role="tablist" aria-label="内容分类">
  <button class="tab is-selected" type="button" role="tab" aria-selected="true" aria-controls="panel-all">全部</button>
  <button class="tab" type="button" role="tab" aria-selected="false" aria-controls="panel-recent">最近</button>
</div>
<section id="panel-all" role="tabpanel">...</section>
<section id="panel-recent" role="tabpanel" hidden>...</section>
```

表格或页面分区需要更轻的样式时使用 `.tabs-line` 包裹同样的 `.tab`。不要用页签伪造 WisePen 主导航。

## 面包屑

只用于页面自身的本地层级；前序项使用按钮，不跳出 iframe。

```html
<nav class="breadcrumb" aria-label="当前位置">
  <button class="crumb" type="button">课程</button>
  <span aria-hidden="true">/</span>
  <button class="crumb" type="button">第一章</button>
  <span aria-hidden="true">/</span>
  <span class="crumb is-current" aria-current="page">练习</span>
</nav>
```

如果没有真实的页内层级切换，直接省略面包屑。

## 禁止的壳层结构

不要使用或扩展 `.app`、`.sidebar`、`.sidebar-nav`、`.sidebar-footer`、`.nav-item` 来模拟 WisePen 宿主。多分区内容优先使用页签、步骤或普通内容分区。
