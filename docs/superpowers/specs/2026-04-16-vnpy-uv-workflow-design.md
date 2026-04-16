# vn.py 使用 uv 的开发环境与安装流程设计

日期：2026-04-16

## 背景

当前仓库已经具备标准的 Python 项目结构：

- 使用 [pyproject.toml](C:/Users/sai/project/vnpy/.worktrees/xt-first/pyproject.toml) 管理项目元数据与依赖
- 使用 `hatchling` 作为构建后端
- 通过 [install.bat](C:/Users/sai/project/vnpy/.worktrees/xt-first/install.bat) 与 [install.sh](C:/Users/sai/project/vnpy/.worktrees/xt-first/install.sh) 调用 `pip install` 完成安装

现有方案的问题不在于“不能安装”，而在于“难以长期稳定管理开发环境”：

- 安装脚本依赖当前 shell 中的 `python`
- 不负责统一虚拟环境入口
- 不提供锁文件能力
- 团队成员日常运行测试、脚本、增删依赖时缺少统一命令
- 在 Windows/MSYS/不同 Python 共存的环境里，容易装到错误解释器

因此，本次目标不是重做发布体系，而是把项目的开发环境管理标准化到 `uv`。

## 目标

本次调整只解决以下问题：

1. 让项目默认使用 `uv` 管理 Python 开发环境与依赖同步
2. 保留现有 `hatchling` 构建方式，不改动发布打包主线
3. 保留 `install.bat` 和 `install.sh`，但将其调整为兼容入口，而不是主安装逻辑
4. 在 README 中明确推荐 `uv sync`、`uv run` 作为标准开发命令
5. 让开发、测试、脚本运行都走统一入口，减少解释器混乱

## 非目标

本次不做以下事情：

- 不重构项目发布流程
- 不替换 `hatchling`
- 不重写 CI
- 不批量迁移所有历史脚本
- 不改动项目业务代码
- 不处理 `vnpy_xt`、QMT、数据库历史源等功能问题

## 设计选择

采用以下策略：

- `uv` 负责：
  - Python 解释器选择
  - 虚拟环境管理
  - 依赖同步
  - 开发命令执行
- `hatchling` 继续负责：
  - wheel/sdist 构建
  - 现有 build hook

这意味着项目将形成“两层分工”：

- 开发层：`uv`
- 构建层：`hatchling`

这种组合兼容当前仓库结构，也避免无意义地重做发布体系。

## 用户工作流

迁移完成后，推荐工作流如下：

### 首次初始化

```bash
uv sync --extra alpha --extra dev
```

### 运行测试

```bash
uv run pytest
```

### 运行单个 Python 命令

```bash
uv run python -c "import vnpy; print(vnpy.__version__)"
```

### 运行项目脚本

```bash
uv run python run.py
```

## 安装脚本策略

保留现有安装脚本，但角色改变：

- [install.bat](C:/Users/sai/project/vnpy/.worktrees/xt-first/install.bat)
- [install.sh](C:/Users/sai/project/vnpy/.worktrees/xt-first/install.sh)

它们不再直接承担完整的 `pip install` 流程，而是：

1. 检查 `uv` 是否可用
2. 给出清晰错误提示或引导安装 `uv`
3. 调用统一的 `uv sync` 安装流程

这样可以兼容旧入口，同时把实际环境管理逻辑收敛到 `uv`。

## 依赖策略

现有 [pyproject.toml](C:/Users/sai/project/vnpy/.worktrees/xt-first/pyproject.toml) 已经定义了：

- 默认依赖
- `alpha` extra
- `dev` extra

因此不需要引入新的依赖清单文件。

推荐默认开发安装命令为：

```bash
uv sync --extra alpha --extra dev
```

如果需要更轻量的用户安装，可继续支持：

```bash
uv sync
```

## 文档策略

README 调整原则：

- 安装章节以 `uv` 为第一推荐方式
- 原有脚本入口保留，但降级为兼容方式
- 测试、脚本运行、开发说明统一改写为 `uv run ...`

中英文 README 都需要同步，避免仓库出现双轨说明。

## 变更范围

本次实现建议只修改这些文件：

- [pyproject.toml](C:/Users/sai/project/vnpy/.worktrees/xt-first/pyproject.toml)
- [install.bat](C:/Users/sai/project/vnpy/.worktrees/xt-first/install.bat)
- [install.sh](C:/Users/sai/project/vnpy/.worktrees/xt-first/install.sh)
- [README.md](C:/Users/sai/project/vnpy/.worktrees/xt-first/README.md)
- [README_ENG.md](C:/Users/sai/project/vnpy/.worktrees/xt-first/README_ENG.md)

可选新增：

- `uv.lock`

## 风险与处理

### 1. 旧用户仍然习惯运行安装脚本

处理方式：
- 保留脚本
- 让脚本内部调用 `uv`

### 2. 某些依赖在特定平台安装较慢或较脆弱

处理方式：
- 优先保留现有依赖定义
- 只迁移环境管理方式，不重写依赖结构

### 3. 团队成员仍混用 `python` / `pip`

处理方式：
- README 明确以 `uv run`、`uv sync` 为标准命令
- 脚本入口也统一到 `uv`

## 结论

本次 `uv` 迁移不应被理解为“更换打包后端”，而应理解为“把开发环境管理标准化”。

最终形态应当是：

- 项目继续使用 `hatchling` 构建
- 项目默认使用 `uv` 进行环境与依赖管理
- 安装脚本保留，但变成 `uv` 的兼容入口
- README 以 `uv` 为主，`pip` 为辅

这是当前仓库收益最高、风险最低的迁移方式。
