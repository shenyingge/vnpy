# XTQuant 与 vnpy_xt 一年分钟线回测验证设计

日期：2026-04-17

## 背景

当前项目已经完成了 `stock_a` 研究链路的第一阶段接入：

- `StockAResearchDatafeed` 可以消费 XT 风格的历史数据源；
- `import_bar_history` 可以将 `BarData` 写入 `AlphaLab`；
- `BacktestingEngine` 可以从 `AlphaLab` 读取数据并执行简单回测；
- 外部标的写法已经统一为 QMT/迅投风格，例如 `600000.SH`、`000001.SZ`。

现在需要进一步验证“真实 XT 数据源”是否能贯通到研究与回测主线，而不仅仅是使用测试桩数据跑通流程。

用户本地已有一个更高版本的 XT Python 包压缩包：

- `C:\Users\sai\project\vnpy\xtquant_250807.rar`

同时，`vnpy_xt` 的官方安装依赖中会带上一个较旧版本的 `xtquant`。如果先解压本地 `xtquant`，再安装 `vnpy_xt`，本地较新版本很可能会被覆盖，导致版本不符合用户预期。

因此，本次设计需要同时解决两件事：

1. 在当前 `.venv` 中建立一个“以 `vnpy_xt` 为主、以本地更新版 `xtquant` 覆盖”的可运行环境；
2. 用真实工业富联 `601138.SH` 过去 1 年的 1 分钟历史数据验证 `xtquant -> vnpy_xt -> stock_a -> AlphaLab -> BacktestingEngine` 全链路是否畅通。

## 目标

本次交付目标是一次“真实环境验证”，而不是安装工具开发。

需要完成：

1. 在当前工作树 `.venv` 中安装 `vnpy_xt`；
2. 将本地 `xtquant_250807.rar` 解压覆盖到当前 `.venv` 的 `site-packages`；
3. 验证 `xtquant`、`vnpy_xt`、`XtDatafeed` 能在同一环境中正常导入；
4. 通过 `XtDatafeed` 获取工业富联 `601138.SH` 在 `2025-04-17` 到 `2026-04-17` 的 1 分钟历史数据；
5. 通过现有 `stock_a` research 入口导入 `AlphaLab`；
6. 执行一次简单 round-trip 回测，验证订单、成交和最终持仓状态。

## 方案选择

### 方案 A：只验证 xtquant 拉数

只把 `xtquant` 解压到当前环境，然后写一个独立脚本调用 `xtdata` 下载和读取 `601138.SH` 的一年分钟数据。

优点：

- 最快；
- 对当前项目代码侵入最小。

缺点：

- 只能验证 `xtquant` 自身可用；
- 无法证明 `vnpy_xt` 和项目现有回测链路可用。

### 方案 B：直接桥接 xtquant 到 stock_a

跳过 `vnpy_xt`，直接使用 `xtquant.xtdata` 获取历史数据，在项目内临时转换为 `BarData` 再导入回测。

优点：

- 能同时验证真实数据和回测链路；
- 不依赖 `vnpy_xt` 安装。

缺点：

- 会引入一条临时旁路；
- 偏离当前“尽量借鉴 `vnpy_xt`”的设计原则；
- 不利于后续收敛到正式生产方案。

### 方案 C：以 vnpy_xt 为主链路，解压本地 xtquant 覆盖

先安装 `vnpy_xt`，再将本地较新版本 `xtquant` 解压覆盖到当前 `.venv`，然后通过 `XtDatafeed` 进入现有 `stock_a` 研究与回测链路。

优点：

- 与当前项目设计原则一致；
- 最大限度复用 `vnpy_xt` 的历史数据接入方式；
- 能验证最接近后续正式运行形态的链路。

缺点：

- 安装与版本覆盖顺序需要严格控制；
- 需要处理 `vnpy_xt` 自带旧版 `xtquant` 的覆盖问题。

本次选择方案 C。

## 安装顺序设计

安装顺序必须固定为：

1. 在当前 `.venv` 中安装 `vnpy_xt`
2. 再将 `xtquant_250807.rar` 解压覆盖到 `.venv\Lib\site-packages`
3. 最后做导入探活和真实数据验证

不能反过来执行。

原因：

- `vnpy_xt` 安装时会依赖一个较旧版本的 `xtquant`；
- 先解压本地 `xtquant` 再安装 `vnpy_xt`，会把本地较新文件覆盖掉；
- 先安装 `vnpy_xt`，再用本地压缩包覆盖，才能保证最终环境以用户本地版本为准。

本次只做“手工自动化执行”这一步，不做长期安装脚本封装。

## 组件边界

### 1. xtquant

职责：

- 与本地 MiniQMT/QMT 连接；
- 下载和读取历史行情缓存；
- 提供 `vnpy_xt` 所依赖的 XT Python 运行环境。

本次不直接把 `xtquant` 作为项目对外研究接口。

### 2. vnpy_xt

职责：

- 提供 `XtDatafeed`；
- 将 XT/QMT 历史数据转成 `HistoryRequest -> list[BarData]` 的 vn.py 风格接口。

本次真实历史数据验证必须优先通过 `XtDatafeed` 进入项目。

### 3. stock_a research 入口

职责：

- 继续复用 `StockAResearchDatafeed`、`import_bar_history`、`AlphaLab`；
- 保持当前 `stock_a` 研究链路不绕过 `vnpy_xt`；
- 负责将真实数据接入后导入研究缓存并驱动回测。

### 4. 回测验证层

职责：

- 使用最小 round-trip 策略；
- 验证数据导入后能被 `BacktestingEngine` 正常消费；
- 验证订单、成交和最终持仓归零。

本次不扩展复杂策略逻辑，不验证收益分析指标。

## 验证数据设计

本次真实验证固定使用：

- 标的：`601138.SH`（工业富联）
- 周期：`1m`
- 时间范围：`2025-04-17` 到 `2026-04-17`
- 外部写法：QMT/迅投风格 `601138.SH`
- 内部 vt_symbol：转换为 `601138.SSE`

设计意图：

- 使用 A 股真实股票而不是指数或 ETF；
- 使用过去 1 年分钟线，覆盖足够长的真实历史窗口；
- 与用户当前对 `.SH/.SZ` 写法的要求一致。

## 执行流程设计

### 环境准备

1. 确认当前工作树 `.venv` 可被 `uv` 使用；
2. 安装 `vnpy_xt`；
3. 解压 `xtquant_250807.rar` 到当前 `.venv` 的 `site-packages`；
4. 验证以下导入：
   - `import xtquant`
   - `import vnpy_xt`
   - `from vnpy_xt.xt_datafeed import XtDatafeed`

### 历史数据准备

1. 通过 XT 侧接口补齐 `601138.SH` 的一年 1 分钟历史；
2. 使用 `XtDatafeed` 按 `HistoryRequest` 拉取该区间分钟线；
3. 确认返回 `BarData` 数量大于 0；
4. 确认返回时间语义能兼容当前 `stock_a` 的中国市场时间处理方式。

### 研究链路验证

1. 将真实 `BarData` 通过 `StockAResearchDatafeed` / `import_bar_history` 导入 `AlphaLab`；
2. 为 `601138.SSE` 添加回测所需合约配置；
3. 使用现有简单 round-trip 策略执行回测；
4. 检查订单、成交、最终仓位等关键状态。

## 失败分类

为了方便快速定位问题，本次失败必须按三类区分：

### 1. 安装失败

表现：

- `vnpy_xt` 无法安装；
- 本地 `xtquant` 覆盖后导入失败；
- Python 版本与 `.pyd` 不匹配。

结论：

- 问题位于环境层，不应继续误判为数据或回测问题。

### 2. XT 连接或权限失败

表现：

- MiniQMT/QMT 未启动；
- XT 无法连接；
- 历史数据无法下载；
- 本地行情缓存为空；
- `XtDatafeed` 查询返回空数据或报连接错误。

结论：

- 环境安装可能已成功，但本机 XT 运行条件不满足。

### 3. 回测链路失败

表现：

- 能成功拉到真实历史数据；
- 但在导入 `AlphaLab`、加载历史、执行策略或撮合时失败。

结论：

- 问题位于研究与回测主线，而不是 XT 环境本身。

## 成功标准

本次验证成功必须同时满足：

1. 当前 `.venv` 中 `xtquant` 和 `vnpy_xt` 可共同导入；
2. `XtDatafeed` 能成功获取工业富联一年分钟线；
3. 返回 `BarData` 数量大于 0；
4. 数据能成功写入 `AlphaLab`；
5. `BacktestingEngine` 能完整跑完回测；
6. 能看到非空订单与成交；
7. 策略最终仓位归零；
8. 留下一份可重复执行的运行说明。

## 不在本次做的事情

本次明确不做：

- 不开发自动化安装脚本；
- 不修改 `install.bat`、`install.sh` 等现有安装脚本；
- 不实现 `xtquant` 自动部署工具；
- 不扩展到多标的、多策略、多周期验证；
- 不引入正式的生产级数据下载调度逻辑；
- 不处理实盘交易链路。

## 需求记录

虽然本次不实现自动化工具，但需要显式记录后续需求：

后续应补一个项目内工具，用于自动完成以下动作：

1. 安装 `vnpy_xt`
2. 解压本地 `xtquant` 压缩包到目标 Python 环境
3. 进行导入探活
4. 输出当前环境中 `xtquant` / `vnpy_xt` 的版本与来源

该工具应优先面向 `uv` 管理的项目环境，但本次不进入实现范围。

## 结论

本次最合适的方案，是以 `vnpy_xt` 为主链路，先安装 `vnpy_xt`，再用本地更新版 `xtquant` 覆盖，最后用工业富联过去 1 年分钟线验证：

`xtquant -> vnpy_xt.XtDatafeed -> stock_a -> AlphaLab -> BacktestingEngine`

这样既能保持设计干净，也能最大限度接近后续正式运行方式。
