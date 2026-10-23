# 颜色、表面与状态变量

页面补充样式只使用本文件标为公开的变量。优先复用组件 class，不复制组件的 hover、focus、disabled 或 selected 样式。

## 页面和文字

| 变量 | 用途 |
|---|---|
| `--background` | 页面画布背景 |
| `--foreground` | 正文和主要标题，不用纯黑代替 |
| `--muted` | 辅助说明和次要信息 |
| `--text-tertiary` | 占位符和低优先级信息 |
| `--surface` | 卡片、表格行和普通内容表面 |
| `--surface-secondary` | 次级内容表面 |
| `--surface-tertiary` | 弱背景、骨架和局部衬底 |
| `--surface-hover` | 普通表面悬停背景 |
| `--overlay` | 弹窗、菜单和浮层表面 |

不要使用 `--black`、`--white`。强调色上的文字由对应 `*-foreground` 变量或组件 class 决定。

## 边框和分隔

| 变量 | 用途 |
|---|---|
| `--border` | 常规边框 |
| `--border-light` | 卡片、提示条等浅边框 |
| `--separator` | 内容分隔线 |

## 普通控件

| 变量 | 用途 |
|---|---|
| `--default` | 次按钮、普通标签和普通控件背景 |
| `--default-foreground` | 普通控件文字 |
| `--default-hover` | 普通控件悬停背景 |

## WisePen 强调色

| 变量 | 用途 |
|---|---|
| `--accent` | 主按钮、进度和核心强调 |
| `--accent-hover` | 实心强调控件悬停背景 |
| `--accent-foreground` | 实心强调背景上的文字 |
| `--accent-text` | 强调文字、次按钮文字 |
| `--accent-text-strong` | 强选中态文字 |
| `--accent-soft` | 轻量选中、进行中背景 |
| `--accent-softer` | 表头、行悬停等更浅背景 |
| `--accent-soft-hover` | 浅强调控件悬停背景 |
| `--accent-border` | 强调态浅边框 |
| `--focus` | 输入和键盘焦点色 |

一个区域至多有一个主操作。不要把强调色当作大面积装饰背景。

## 表单字段

| 变量 | 用途 |
|---|---|
| `--field-bg` | 输入控件背景 |
| `--field-bg-hover` | 输入控件悬停背景 |
| `--field-border` | 输入控件边框 |
| `--field-border-hover` | 输入控件悬停边框 |
| `--field-border-focus` | 输入控件聚焦边框 |
| `--field-foreground` | 输入内容文字 |
| `--field-placeholder` | 输入占位文字 |

优先使用 `.input`、`.textarea`、`.select`，不要自行复刻字段状态。

## 状态色

状态色含义固定，不跟随 aqua 主题改变，也不能因装饰需要互换。

| 状态 | 实色 | 实色文字 | 状态文字 | 软背景 | 边框 | 额外状态 |
|---|---|---|---|---|---|---|
| 信息 | `--info` | `--info-foreground` | `--info-text` | `--info-soft` | `--info-border` | 无 |
| 成功 | `--success` | `--success-foreground` | `--success-text` | `--success-soft` | `--success-border` | 无 |
| 警告 | `--warning` | `--warning-foreground` | `--warning-text` | `--warning-soft` | `--warning-border` | 无 |
| 危险 | `--danger` | `--danger-foreground` | `--danger-text` | `--danger-soft` | `--danger-border` | `--danger-hover`、`--danger-soft-hover` |

- 信息：客观提示、同步状态。
- 成功：完成、通过、有效。
- 警告：待确认、需要注意、可能有影响。
- 危险：失败、删除、不可逆操作。

普通页面扩展优先使用状态文字、软背景和边框；实色优先交给已有组件。

## 阴影和遮罩

| 变量 | 用途 |
|---|---|
| `--surface-shadow` | 普通表面和轻量卡片 |
| `--card-shadow` | 需要更明显层级的卡片 |
| `--overlay-shadow` | 菜单和弹窗 |
| `--backdrop` | 模态遮罩 |

不得创建新的 `box-shadow` 数值。遮罩只用于真实打开的模态界面。

## 非公开颜色变量

以下变量由组件内部管理，页面 CSS 不直接使用：

- `--selection`；
- `--control-disabled-border`、`--control-disabled-fg`、`--control-disabled-filled-bg`、`--control-disabled-filled-fg`、`--control-disabled-soft-bg`、`--control-disabled-soft-fg`；
- `--table-chrome-bg`、`--table-inner-border`、`--table-row-hover-bg`、`--table-row-selected-bg`、`--table-row-selected-hover-bg`；
- `--sidebar-surface`、`--item-hover`、`--item-selected`、`--item-selected-hover`。

通过 `disabled`、`.is-selected`、`.is-invalid` 等结构状态触发对应样式。
