# 布局、排版与尺寸变量

页面专用 CSS 可使用本文件标为公开的变量。`grid`、`flex`、`auto`、百分比、`fr` 和必要的 `min()`、`max()`、`clamp()` 可用于结构；视觉尺寸不要写任意裸像素。

## 间距

从小到大：

| 变量 | 典型用途 |
|---|---|
| `--space-3xs` | 极小的内部间隔 |
| `--space-2xs` | 图标或紧凑内容间隔 |
| `--space-2xs-plus` | 小型控件内部间隔 |
| `--space-xs` | 紧凑组件间距 |
| `--space-sm` | 普通控件和按钮组间距 |
| `--space-md` | 卡片内边距、表单字段间距 |
| `--space-md-plus` | 中等偏大区块间距 |
| `--space-lg` | 内容区块间距 |
| `--space-xl` | 页面级留白 |
| `--space-2xl` | 大区块分隔 |

优先使用 `.stack`、`.row`、`.cluster` 和 `.gap-*`。只有缺少相应结构时才在页面 class 中使用间距变量。

## 字体和行高

| 变量组 | 用途 |
|---|---|
| `--font-sans` | 普通界面字体 |
| `--font-mono` | 代码和机器标识符 |
| `--font-size-2xs` | 极小辅助信息，谨慎使用 |
| `--font-size-xs` | 字段提示和少量元信息 |
| `--font-size-sm`、`--font-size-base` | 正文和控件文字 |
| `--font-size-lg` | 强调正文 |
| `--font-size-heading-1`、`--font-size-heading-2`、`--font-size-heading-3`、`--font-size-heading-4`、`--font-size-heading-5` | 标题层级 |
| `--font-weight-regular` | 普通正文 |
| `--font-weight-medium` | 控件、卡片标题 |
| `--font-weight-semibold` | 页面标题、表单标签 |
| `--font-weight-bold` | 极少量强强调 |
| `--line-height-2xs`、`--line-height-xs`、`--line-height-sm`、`--line-height-md`、`--line-height-base` | 对应内容行高 |

标题优先使用 `.page-title`、`.section-title`、`.title-2`、`.title-3`；正文使用 `.body`，辅助说明使用 `.meta`。不要为同一语义重新拼装字号、字重和行高。

## 圆角

| 变量 | 用途 |
|---|---|
| `--app-radius-inline` | 进度、代码等紧凑元素 |
| `--app-radius-field` | 输入和上传区域 |
| `--app-radius-icon` | 图标按钮 |
| `--app-radius-content` | 卡片、提示和表格外壳 |
| `--app-radius-popover` | 菜单和浮层 |
| `--app-radius-modal` | 模态框 |
| `--app-radius-button` | 普通按钮 |
| `--app-radius-pill` | 仅头像、步骤点、单选点和用户胶囊 |

不要使用通用 `--radius`。普通按钮、卡片和输入框不得使用 `--app-radius-pill`。

`--app-radius-checkbox`、`--app-radius-menu-item`、`--app-radius-tooltip`、`--app-radius-detail` 由相应组件内部管理，不用于页面扩展。

## 控件和内容尺寸

| 变量 | 用途 |
|---|---|
| `--control-height-sm` | 紧凑控件高度 |
| `--control-height-md` | 默认控件高度 |
| `--control-height-lg` | 强调控件高度 |
| `--icon-button-size` | 默认图标按钮外框 |
| `--icon-button-size-sm` | 紧凑图标按钮外框 |
| `--icon-glyph-size` | 默认图标尺寸 |
| `--card-narrow-width` | 居中单卡最大宽度 |

表格的 `--table-row-height`、`--table-header-row-height`、`--table-action-column-width` 和 `--table-shell-padding-inline` 由 `.table`、`.table-shell` 管理，页面 CSS 不直接覆盖。

`--sidebar-width` 不对内嵌页面开放；不要制作宿主式侧栏。

## 动效

| 变量 | 用途 |
|---|---|
| `--motion-duration-fast` | 按钮、悬停等即时反馈 |
| `--motion-duration-mid` | 面板和状态变化 |
| `--motion-ease-standard` | 标准缓动 |

只为状态反馈添加短动效。不得持续闪烁、自动播放大幅动画或覆盖 `prefers-reduced-motion` 行为。

## 层级变量

`--z-popover`、`--z-tooltip`、`--z-modal`、`--z-toast` 是组件内部变量。使用 `.menu`、`.tooltip`、`.modal-backdrop` 等组件获得正确层级，不在页面 CSS 中直接使用。

## 响应式原则

- 默认采用单列或能自然收缩的 Grid/Flex；不要假设桌面宽度。
- 窄窗口中按钮组允许换行，表格在 `.table-shell` 内横向滚动。
- 使用正常文档滚动，不给 `html`、`body` 或根容器设置 `overflow: hidden`。
- 除真实模态遮罩外不使用 `position: fixed`。
- 不自行重设 `body` 的字体、背景和文字色。
