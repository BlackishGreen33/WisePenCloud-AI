# 操作与表单组件

所有交互都局限在当前页面。不得制作登录、注册、密码、支付、Token、账号安全或权限配置表单，也不得声称数据已保存到 WisePen 或云端。

## 图标

使用内联 SVG，不引用图标库：

```html
<svg viewBox="0 0 24 24" aria-hidden="true">
  <path d="M12 5v14M5 12h14"></path>
</svg>
```

`tokens.css` 已设置尺寸、无填充、描边、线帽和连接样式。纯图标按钮必须在按钮上写有意义的 `aria-label`。

## 按钮

```html
<button class="btn" type="button">次要操作</button>
<button class="btn btn-primary" type="button">主操作</button>
<button class="btn btn-ghost" type="button">弱操作</button>
<button class="btn btn-danger-soft" type="button">删除</button>
<button class="btn btn-danger" type="button">确认删除</button>
<button class="btn btn-primary" type="button" disabled>处理中</button>
<button class="icon-btn" type="button" aria-label="更多">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 12h.01M12 12h.01M18 12h.01"></path></svg>
</button>
```

- `.btn`：次按钮；灰底、强调色文字、无描边。
- `.btn-primary`：主按钮；一个操作区域至多一个。
- `.btn-ghost`：低优先级操作。
- `.btn-danger-soft`：普通删除入口；只有最终不可逆确认才用 `.btn-danger`。
- `.btn-sm`、`.btn-lg`：紧凑和强调高度。
- `.icon-btn`、`.icon-btn-sm`：无文字工具按钮。
- 图标按钮选中加 `.is-active`，危险图标加 `.is-danger`。

有文字的按钮若使用图标，图标放在文字前。不要用 `<a href="#">` 伪造按钮或导航。

## 字段

```html
<form class="stack gap-md" id="settings-form">
  <label class="field">
    <span class="field-label">名称</span>
    <input class="input" name="name" type="text" placeholder="请输入名称" required>
    <span class="field-hint">用于当前页面内的展示</span>
  </label>

  <label class="field">
    <span class="field-label">说明</span>
    <textarea class="textarea" name="description" rows="4" placeholder="补充说明"></textarea>
  </label>

  <label class="field">
    <span class="field-label">显示方式</span>
    <select class="select" name="mode">
      <option value="list">列表</option>
      <option value="cards">卡片</option>
    </select>
  </label>

  <button class="btn btn-primary" type="submit">应用到当前页面</button>
</form>
```

脚本必须阻止默认提交，只更新当前页面状态：

```js
document.querySelector("#settings-form").addEventListener("submit", (event) => {
  event.preventDefault();
  // 读取 FormData，并安全地更新当前页面。
});
```

不要写 `action`，不要发送网络请求，不要把“应用到当前页面”写成“保存到云端”。用户输入通过 `textContent` 写回，不放入 `innerHTML`。

## 搜索框

搜索只过滤当前页面已有数据。

```html
<label class="input-wrap">
  <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="6"></circle><path d="M20 20l-3.5-3.5"></path></svg>
  <input class="input" type="search" placeholder="筛选当前列表">
</label>
```

## 错误状态

字段错误时给控件添加 `.is-invalid`，并提供文字：

```html
<label class="field">
  <span class="field-label">数量</span>
  <input class="input is-invalid" type="number" aria-invalid="true" aria-describedby="count-error">
  <span class="field-error" id="count-error">请输入有效数量</span>
</label>
```

不要只靠颜色表达错误。

## 选择控件

```html
<label class="check"><input type="checkbox"> 显示已完成项</label>
<label class="radio"><input type="radio" name="scope" checked> 全部内容</label>
<label class="switch"><input type="checkbox" checked><span class="switch-track"></span> 显示提示</label>
```

使用原生 `checked`、`disabled` 和键盘行为，不用普通 `div` 模拟控件。

## 本地文件

只有用户明确要求浏览器内读取文件时才展示本地文件选择；不得声称文件会上传或保存。展示区使用 `.upload`，实际选择使用可访问的 `<input type="file">`，并在文案中说明“仅在当前页面处理”。
