# 提示、菜单与模态组件

## 提示条

```html
<div class="banner banner-info" role="status">
  <div class="stack gap-3xs">
    <strong class="body">提示标题</strong>
    <span class="meta">补充说明保持简短明确。</span>
  </div>
  <button class="btn btn-sm" type="button">查看</button>
</div>
```

可用状态：

- `.banner-accent`：当前内容或 WisePen 强调；
- `.banner-info`：客观信息；
- `.banner-success`：成功结果；
- `.banner-warning`：需要注意或待确认；
- `.banner-danger`：失败或危险结果。

提示条保持普通表面，只让标题体现状态色。没有真实可执行动作时省略按钮。动态提示根据重要性使用 `role="status"` 或 `role="alert"`，不要滥用 `alert`。

## 模态框

只有当前页面内确实需要中断式确认时才使用。打开时显示 `.modal-backdrop`，关闭时给它设置 `hidden`。

```html
<div class="modal-backdrop" id="confirm-dialog" hidden>
  <section class="modal" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
    <header class="modal-header">
      <h2 id="confirm-title" class="title-3">确认删除</h2>
      <button class="icon-btn" type="button" aria-label="关闭确认框">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7l10 10M17 7L7 17"></path></svg>
      </button>
    </header>
    <div class="modal-body">
      <p class="body">删除后只影响当前页面内的数据。</p>
    </div>
    <footer class="modal-footer">
      <button class="btn" type="button">取消</button>
      <button class="btn btn-danger" type="button">确认删除</button>
    </footer>
  </section>
</div>
```

脚本需要：

- 打开后把焦点移入模态框；
- Escape 和取消按钮关闭；
- 关闭后把焦点还给触发按钮；
- 打开期间避免焦点进入背后内容；
- 不把普通说明卡片做成模态框。

标题保持中性色，不要把整窗变红。只有最终不可逆操作使用 `.btn-danger`。

## 菜单

```html
<div class="menu" role="menu" hidden>
  <div class="menu-label">项目操作</div>
  <button class="menu-item" type="button" role="menuitem">重命名</button>
  <button class="menu-item" type="button" role="menuitem">复制内容</button>
  <button class="menu-item is-danger" type="button" role="menuitem">删除</button>
</div>
```

菜单由相邻的 `.icon-btn` 触发，并同步 `aria-expanded`。实现方向键、Escape 和点击外部关闭；关闭后恢复触发按钮焦点。菜单项执行当前页面内动作，不提供外部链接、下载或宿主导航。

只有一两个动作时直接显示按钮，不额外使用菜单。

## Tooltip

```html
<div class="tooltip" role="tooltip" id="filter-tip" hidden>筛选当前列表</div>
```

Tooltip 只补充无文字控件含义，不能承载必要信息。触发控件仍需 `aria-label`，并通过 `aria-describedby` 关联 Tooltip。鼠标悬停和键盘聚焦都能显示，离开时隐藏；不要一经过就立即弹出。

## 分隔线

```html
<hr class="separator">
```

只在内容分组确实需要视觉分隔时使用，不用多个空分隔线制造间距。

## 本地状态反馈

页面交互完成后，优先更新就近的文字、标签或 `aria-live="polite"` 状态区域：

```html
<p class="meta" aria-live="polite" id="operation-status"></p>
```

状态文案应说明“已应用到当前页面”“已从当前列表移除”等真实结果，不写“已保存到云端”“已同步”或“已通知用户”等未实现能力。
