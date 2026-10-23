# 数据展示组件

## 状态标签

```html
<span class="chip">草稿</span>
<span class="chip chip-accent">进行中</span>
<span class="chip chip-info">同步信息</span>
<span class="chip chip-success">已完成</span>
<span class="chip chip-warning">待确认</span>
<span class="chip chip-danger">失败</span>
```

标签文字必须描述真实状态。`.chip-accent` 表示当前或进行中，不替代信息、成功、警告和危险语义。

## 卡片

```html
<section class="card">
  <header class="card-header">
    <h2 class="title-3">学习进度</h2>
    <span class="chip chip-accent">进行中</span>
  </header>
  <div class="card-body stack gap-sm">
    <p class="body">卡片正文使用正常正文样式。</p>
    <p class="meta">辅助信息放在这里。</p>
  </div>
</section>
```

卡片用于真实的信息分组，不要把页面每一段都装进卡片。`.card-narrow` 只用于居中单卡。

## 表格

```html
<div class="table-shell">
  <div class="table-toolbar">
    <label class="input-wrap">
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"></circle><path d="M20 20l-3.5-3.5"></path></svg>
      <input class="input" type="search" placeholder="筛选当前表格">
    </label>
    <span class="spacer"></span>
    <button class="btn btn-primary btn-sm" type="button">新增项目</button>
  </div>
  <table class="table">
    <thead>
      <tr>
        <th scope="col">名称</th>
        <th scope="col">状态</th>
        <th scope="col">更新时间</th>
        <th scope="col" class="col-action"><span class="sr-only">操作</span></th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>课程大纲</td>
        <td><span class="chip chip-success">已完成</span></td>
        <td>今天 18:20</td>
        <td class="col-action"><button class="icon-btn" type="button" aria-label="打开课程大纲操作菜单">...</button></td>
      </tr>
    </tbody>
  </table>
</div>
```

- 操作列用 `.col-action` 和图标按钮。
- 选中行加 `.is-selected`，并用 `aria-selected="true"` 表达状态。
- `.table-shell` 负责窄窗口横向滚动，不要让整页横向溢出。
- 空数据时不要保留空表格，改用空状态。

## 空状态

```html
<div class="empty">
  <strong class="title-3">还没有项目</strong>
  <p class="meta">添加项目后会显示在这里。</p>
  <button class="btn btn-primary" type="button">添加项目</button>
</div>
```

只展示当前页面能够真正执行的操作。

## 进度

```html
<div class="progress">
  <span class="progress-label">完成进度</span>
  <span class="progress-value">42%</span>
  <div class="progress-track" role="progressbar" aria-label="完成进度" aria-valuemin="0" aria-valuemax="100" aria-valuenow="42">
    <div class="progress-fill" style="width: 42%"></div>
  </div>
</div>
```

动态百分比是允许使用内联 `style` 的少数例外；值必须与 `aria-valuenow` 和可见文字一致，并限制在 0–100%。

## 步骤

```html
<ol class="steps" aria-label="完成步骤">
  <li class="step is-done"><span class="step-dot"></span>填写</li>
  <li class="step is-active" aria-current="step"><span class="step-dot"></span>确认</li>
  <li class="step"><span class="step-dot"></span>完成</li>
</ol>
```

`.is-done` 表示已完成，`.is-active` 表示当前步骤。不要把步骤条当成装饰。

## 骨架

```html
<div class="skeleton" aria-hidden="true"></div>
```

骨架只用于确实存在的短暂本地计算或切换状态。页面没有异步加载时不要展示假骨架。宽度差异通过页面专用 class 定义，不使用无意义的随机宽度。
