# stock_a 实盘链路复用 vnpy_qmt 设计

日期：2026-04-17

## 背景

当前项目已经确认了三件事：

- 历史数据链路已经以 `xtquant -> vnpy_xt -> stock_a -> AlphaLab -> BacktestingEngine` 跑通；
- `vnpy_qmt` 已被一次性 vendor 到当前工作树，可作为本地长期维护的 fork 源码；
- 后续很可能继续使用 vn.py 自带界面进行连接、监控和操作，因此正式交易边界不能偏离 vn.py 原生的 gateway 设计。

基于对 `vendor/vnpy_qmt` 的源码检查，可以确认：

- [`QmtGateway`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/qmt_gateway.py) 是标准的 vn.py `BaseGateway` 入口；
- [`TD`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/td.py) 封装了 `xtquant.xttrader` 的连接、下单、撤单、查询和回报转换；
- [`MD`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/md.py) 封装了 `xtquant.xtdata` 的订阅和 tick 转换；
- [`utils.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/utils.py) 封装了 QMT 与 vn.py 之间的代码、方向、状态映射。

因此当前问题不再是“要不要复用 `vnpy_qmt`”，而是：

- 如何**完整保留** `vnpy_qmt` 的框架和 gateway 形态；
- 如何在**不绕开它**的前提下补外层安全边界；
- 如何让后续仍能用 vn.py 原生 UI 和回测方案。

## 目标

本次设计目标是明确：

1. `vnpy_qmt` 在当前项目中的正式定位；
2. 哪些修改应直接落在 `vnpy_qmt` 源码内部；
3. 哪些能力适合放在 gateway 外层；
4. 回测和研究链路应如何尽量贴近 vn.py 原生设计。

## 方案选择

### 方案 A：保留 vnpy_qmt 为正式网关，在外层增加安全包装

做法：

- 保持 `QmtGateway` 作为正式 QMT gateway；
- 如有实现问题，直接修改 vendor 进来的 `vnpy_qmt` 源码；
- 需要对外发布时，从本地 fork 源码重新打包安装；
- `probe`、`dry_run`、白名单、确认闸门、资金上限等安全能力放在 gateway 外层；
- 后续 UI 入口仍然走 `MainEngine.add_gateway(QmtGateway)` 这套 vn.py 原生机制。

优点：

- 最符合 vn.py 的设计思路；
- 不会破坏后续使用 vn.py 自带界面的能力；
- 允许把 QMT 实现问题收敛到 `vnpy_qmt` 源码内部修复；
- 外层仍然可以补充安全控制，而不替代 gateway 本身。

缺点：

- 外层安全包装需要专门设计；
- 部分能力需要区分“应该改 gateway 源码”还是“应该写在外层”。

### 方案 B：复用 vnpy_qmt 的部分实现，但由项目自建交易主边界

做法：

- 保留 `TD`、`utils.py` 等作为参考；
- 在项目里自建新的 `stock_a.live` 运行时，成为正式交易边界；
- `QmtGateway` 仅作为参考，不作为正式入口。

优点：

- 可以完全按项目喜好组织代码；
- 外层模型设计更自由。

缺点：

- 会绕开 `vnpy_qmt` 原本的 gateway 设计；
- 会削弱与 vn.py 原生 UI 的兼容性；
- 与用户“框架应完整保留”的要求冲突。

### 方案 C：彻底绕开 vnpy_qmt，只保留 xtquant

做法：

- 直接用 `xtquant` 官方 API 重写所有交易接入；
- 不再把 `vnpy_qmt` 当正式依赖。

优点：

- 理论上边界最自由。

缺点：

- 与当前目标完全不符；
- 会进一步背离 vn.py 原生 gateway 思路；
- 未来 UI、引擎、事件流兼容性最差。

本次选择方案 A。

## 总体结论

`vnpy_qmt` 在当前项目中的正式定位应当是：

- **正式 QMT gateway**
- **需要时可修改源码并重新打包的本地 fork**
- **未来仍可接入 vn.py 原生 UI 的正式交易入口**

更具体地说：

- `vnpy_qmt.QmtGateway` 是正式交易边界；
- 安全控制、运行脚本、自动化验证、配置模板等放在 gateway 外层；
- `vnpy_xt` 继续负责历史数据；
- 回测尽量复用 vn.py 原生方案，不额外自造一套平行引擎。

## 复用与修改边界

### 1. QmtGateway

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/qmt_gateway.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/qmt_gateway.py)

定位：

- 正式保留；
- 不绕开；
- 后续 UI 和正式运行时都应优先围绕它展开。

建议：

- 如果发现配置项不足、生命周期不完整、轮询节奏不合适，这些问题优先在 `QmtGateway` 或其内部依赖里修；
- 不建议再额外造一个与 `QmtGateway` 平行的“正式交易 runtime”。

### 2. TD

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/td.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/td.py)

定位：

- 是 `vnpy_qmt` 内部最关键的交易实现；
- 后续若连接、回报、撤单、查询有问题，应优先直接改这里。

建议：

- 保留 `XtQuantTrader` 的接入方式；
- 保留查询和回报转换主路径；
- 将 `session_id`、错误处理、资源释放、日志、重连等问题收敛到这里修；
- 修改后通过重新打包 `vnpy_qmt` 的方式引入，而不是在项目外层复制一份并另起边界。

### 3. MD

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/md.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/md.py)

定位：

- 仍属于 `vnpy_qmt` 正式网关的一部分；
- 不建议在项目外层再做一套平行行情 gateway。

建议：

- 如果订阅行为、合约加载方式、启动成本过高，可以直接在 `MD` 内部调整；
- 尤其像 `get_contract()` 的全市场扫描，如果未来不合适，应优先在源码内部优化，而不是在外层绕开。

### 4. utils.py

源码：

- [`vendor/vnpy_qmt/vnpy_qmt/utils.py`](/C:/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/vnpy_qmt/utils.py)

定位：

- 是 `vnpy_qmt` 的内部映射层；
- 源头仍应保留在 gateway 包内。

建议：

- 如果映射逻辑有缺陷，优先直接改 `vnpy_qmt` 源码；
- 如果项目外层确实需要消费某些转换结果，应只做很薄的调用侧适配，不要把这里拆出去另做一份“真源”。

## 外层能力应该放什么

虽然不能绕开 `vnpy_qmt` 自己做交易主线，但仍然可以在外层补这些能力：

- 连接前环境检查
- 配置模板与本地配置文件加载
- `probe` 只读探活
- `dry_run` 模式
- 标的白名单
- 资金上限
- 二次确认闸门
- 适合自动化执行的 CLI 或脚本入口

这些能力的原则是：

- **包裹 gateway**
- **不替代 gateway**
- **不改变 vn.py 原生 engine/gateway/event 的关系**

## 与 vn.py 原生 UI 的关系

这是本次设计最重要的约束之一：

- 后续很可能继续使用 vn.py 自带界面；
- 因此正式交易入口必须仍然能通过 `MainEngine.add_gateway(QmtGateway)` 接入；
- 不能把核心交易逻辑移到一个 vn.py UI 不认识的自定义 service 中；
- 外层脚本、探针、CLI 只能是补充入口，而不是唯一入口。

## 与回测方案的关系

回测部分应尽量贴近 vn.py 原生设计：

- 优先复用 vn.py 现有回测能力；
- A 股/QMT 特有的符号、数据、规则差异，只做必要边界适配；
- 不建议为了贴合当前研究代码，再额外发展出一套与 vn.py 平行的回测主线。

当前 `stock_a` 相关研究代码可以继续作为实验性研究辅助层使用，但不应继续无限扩张为正式框架主线。

## 明确不建议的做法

本次明确不建议：

1. 把 `vnpy_qmt` 降级成“只供参考”的实现；
2. 让 `stock_a.live` 或其它自定义 runtime 成为正式交易主边界；
3. 为了安全控制而绕开 `QmtGateway` 自己下单；
4. 让后续运行只能依赖自定义 CLI，而不能回到 vn.py 自带界面；
5. 继续扩张 `vnpy/research`，让其承载正式交易主线。

## 结论

当前最合适的路线是：

- **保留 `vnpy_qmt` 为正式 QMT gateway**
- **如果实现有问题，直接修改其源码并重新打包**
- **外层只做安全包装和运行辅助**
- **历史数据继续走 `vnpy_xt`**
- **回测尽量贴近 vn.py 原生方案**
