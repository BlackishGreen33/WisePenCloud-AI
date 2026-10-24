---
name: wisepen-ui
description: 当用户要求在 WisePen 中创建或修改内嵌页面、学习工具、数据展示、表单、表格、看板、流程、交互式教学材料或 HTML 内容资源时使用。生成使用 WisePen UI 设计系统的 SINGLE_HTML_PAGE。
---

# WisePen 内嵌界面

为 WisePen 生成可作为 `SINGLE_HTML_PAGE` 打开的内嵌内容。它运行在已登录的 WisePen 宿主中，不是独立网站，也不拥有自己的后端。

## 能力边界

适合制作知识卡片、数据展示、课程计划、测验、问卷、计算器、流程演示、待办清单，以及仅在当前页面内生效的筛选、排序、切换和表单交互。

不得生成或自行补充以下模块：

- 登录、注册、退出、找回或修改密码、验证码、OAuth、SSO；
- 用户中心、账号安全、组织、角色和权限管理；
- 会员、订阅、订单、支付、API Key 或 Token 配置；
- WisePen 主导航、全局侧栏、顶部产品栏或另一套完整应用壳；
- 伪造的云端保存、多用户协作、网络同步、消息发送或服务端处理。

遇到超出边界的请求，应说明该能力属于宿主或后端，提出可在单页内完成的本地替代方案，不用无效按钮伪装已经实现。即使用户要求登录页，也不生成；说明 WisePen 已提供身份环境。

## 必须加载的参考

生成页面前必须加载：

1. `references/css-colors.md`：公开颜色、表面、状态和阴影变量；
2. `references/css-layout.md`：公开间距、排版、尺寸、圆角和动效变量；
3. 根据所需组件加载一个或多个组件参考：
   - `references/components-layout.md`
   - `references/components-actions-and-forms.md`
   - `references/components-data-display.md`
   - `references/components-feedback.md`

只使用参考中公开的 class 和 CSS 变量。不要猜测未记录的名称。规范组件能表达需求时直接复用；确实缺少结构时才增加页面专用 class，并在最终回复中说明扩展内容。

## 文档结构

输出完整、单文件、UTF-8 HTML。`<head>` 必须包含：

```html
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>与内容一致的标题</title>
<link rel="stylesheet" href="/singleHtmlPage/assets/wisepen-ui/v1/tokens.css">
```

不得读取、复制、重写或内联 `tokens.css`，不得修改该地址，也不得添加其他外部 stylesheet。页面补充样式统一放在链接之后的 `<style data-wisepen-page>` 中。

默认使用浅色 aqua。只有用户明确要求深色时才给 `<html>` 添加 `data-theme="dark"`。不要生成 CSS 尚未正式提供的 mist、floral、sunset、emerald 或 lavender 主题，也不要重定义 `:root` 主题变量。

## 样式规则

- 优先使用组件 class；页面 CSS 主要负责内容特有的 Grid/Flex 结构和响应式排列。
- 视觉值只能使用参考中标为公开的 `var(--*)`。不写十六进制、RGB、命名色、任意字号、任意圆角或新阴影。
- 不使用 `--black`、`--white`、`--z-popover`、`--z-tooltip`、`--z-modal`、`--z-toast`、Sidebar 变量或组件内部状态变量。
- 正文使用 `--foreground`，辅助文字使用 `--muted`，低优先级文字使用 `--text-tertiary`。
- 状态色必须按信息、成功、警告、危险的真实语义使用。
- 不使用渐变、玻璃拟态、霓虹、装饰性大动画或胶囊化普通按钮。
- 图标使用内联 SVG：`viewBox="0 0 24 24"`、`aria-hidden="true"`，具体尺寸和描边交给组件 CSS。

## 内嵌与交互规则

- 除固定 WisePen stylesheet 外，不引用外部脚本、字体、图片、iframe、CDN、远程 URL 或相对资源。
- 不使用 `fetch`、XHR、WebSocket、EventSource、Beacon 或表单网络提交。
- 不访问 `window.parent`、`window.top`、`window.opener`、宿主 Cookie 或宿主 DOM，不使用 `postMessage`。
- 不使用 `localStorage`、`sessionStorage`、IndexedDB、Service Worker 或浏览器权限。
- 主要内容在 JavaScript 不可用时仍须可见。可选交互只操作当前页面内存状态。
- 不写 `onclick` 等内联事件属性；脚本放在 `</body>` 前并使用 `addEventListener`。表单必须阻止默认提交。
- 使用语义 HTML、可见标签和键盘可操作控件；纯图标按钮必须有 `aria-label`。
- 适应可变 iframe 宽高，使用正常文档滚动；不得锁定 `html` 或 `body`，不得创建第二个整页滚动容器。

## 生成与交付

1. 只生成用户要求的内容，不添加虚构业务区块。
2. 调用 `sandbox_write_file` 写入简短、明确的 `.html` 文件名，不在聊天回复中粘贴整份源码。
3. 用沙箱读取或搜索工具确认固定 stylesheet、完整文档结构和所需内容存在，并确认没有其他外部资源或网络 API。
4. 修正问题后调用 `sandbox_upload_file_to_cloud_drive`。
5. 最终报告文件名、页面用途、使用的组件扩展（如有）和上传结果。没有实际调用成功时，不声称已经创建或上传。
