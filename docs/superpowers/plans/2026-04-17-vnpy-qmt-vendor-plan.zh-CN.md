# vnpy_qmt Vendor 接入 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `vnpy_qmt` 上游源码一次性拉取到当前 `xt-first` 工作树的 `vendor/vnpy_qmt`，去除远程仓库痕迹，并保留可直接阅读、修改、编译的本地源码目录。

**Architecture:** 使用临时目录浅克隆 `vnpy_qmt` 上游仓库，以固定 commit 为基线，把源码复制进当前工作树的 `vendor/vnpy_qmt`，删除 `.git` 等远程管理痕迹，只保留纯源码快照。整个过程不改 `pyproject.toml`、不改安装脚本、也不接入运行逻辑，只完成源码纳入与目录验证。

**Tech Stack:** git, zsh, PowerShell filesystem, GitHub repository `ruyisee/vnpy_qmt`

---

## 文件结构

### 需要新建的文件和目录

- Create: `vendor/vnpy_qmt/`

### 需要修改的文件

- None

### 职责划分

- `vendor/vnpy_qmt/`：保存一次性纳入的 `vnpy_qmt` 本地源码
- 临时克隆目录：只用于拉取和复制，不进入最终仓库

## 已锁定前提

- 当前工作目录为 `C:\Users\sai\project\vnpy\.worktrees\xt-first`
- 上游仓库地址为 `https://github.com/ruyisee/vnpy_qmt.git`
- 当前探测到的基准 commit 为 `16d70d5a7c3b30eae0a679ca17f81ee2b6fd2927`
- 当前探测到的默认分支为 `master`
- 本次不保留 remote 管理结构
- 本次不把 `vendor/vnpy_qmt` 接入当前 Python 环境

### Task 1: 准备临时拉取目录并确认上游基线

**Files:**
- Create: `vendor/vnpy_qmt/`
- Test: shell verification only

- [ ] **Step 1: 清理可能残留的旧临时目录**

```bash
rm -rf /tmp/vnpy_qmt_vendor
mkdir -p /tmp/vnpy_qmt_vendor
```

- [ ] **Step 2: 再次确认上游 HEAD commit**

Run:

```bash
git ls-remote https://github.com/ruyisee/vnpy_qmt.git HEAD
```

Expected:

```text
16d70d5a7c3b30eae0a679ca17f81ee2b6fd2927	HEAD
```

- [ ] **Step 3: 浅克隆上游仓库到临时目录**

Run:

```bash
git clone --depth 1 https://github.com/ruyisee/vnpy_qmt.git /tmp/vnpy_qmt_vendor/src
```

Expected:

```text
Cloning into '/tmp/vnpy_qmt_vendor/src'...
```

- [ ] **Step 4: 验证克隆结果**

Run:

```bash
cd /tmp/vnpy_qmt_vendor/src
git rev-parse HEAD
git branch --show-current
ls
```

Expected:

- `git rev-parse HEAD` 输出 `16d70d5a7c3b30eae0a679ca17f81ee2b6fd2927`
- `git branch --show-current` 输出 `master`
- 根目录能看到如 `setup.py`、`vnpy_qmt/`、`README.md` 等上游项目文件

- [ ] **Step 5: 提交前检查点**

说明：

- 这一任务不产生仓库内变更
- 不提交

### Task 2: 将源码复制到 vendor 目录并去除远程痕迹

**Files:**
- Create: `vendor/vnpy_qmt/`
- Test: shell verification only

- [ ] **Step 1: 删除工作树中可能已有的旧 vendor 目录**

Run:

```bash
rm -rf /c/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt
mkdir -p /c/Users/sai/project/vnpy/.worktrees/xt-first/vendor
```

Expected:

- `vendor/` 存在
- `vendor/vnpy_qmt` 被清空或尚不存在

- [ ] **Step 2: 复制上游源码到当前工作树**

Run:

```bash
cp -R /tmp/vnpy_qmt_vendor/src /c/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt
```

Expected:

- `vendor/vnpy_qmt` 创建成功
- 目录中包含上游源码完整内容

- [ ] **Step 3: 删除 vendor 目录中的 Git 元数据**

Run:

```bash
rm -rf /c/Users/sai/project/vnpy/.worktrees/xt-first/vendor/vnpy_qmt/.git
```

Expected:

- `vendor/vnpy_qmt/.git` 不存在

- [ ] **Step 4: 验证最终目录结构**

Run:

```bash
cd /c/Users/sai/project/vnpy/.worktrees/xt-first
find vendor/vnpy_qmt -maxdepth 2 -type f | sort | head -n 40
test ! -d vendor/vnpy_qmt/.git
```

Expected:

- 输出中能看到关键文件，如：

```text
vendor/vnpy_qmt/README.md
vendor/vnpy_qmt/setup.py
vendor/vnpy_qmt/vnpy_qmt/__init__.py
vendor/vnpy_qmt/vnpy_qmt/qmt_gateway.py
```

- `test ! -d vendor/vnpy_qmt/.git` 成功退出

- [ ] **Step 5: 提交 vendor 源码**

```bash
cd /c/Users/sai/project/vnpy/.worktrees/xt-first
git add vendor/vnpy_qmt
git commit -m "chore: vendor vnpy_qmt source"
```

### Task 3: 验证工作树边界不被额外扩大

**Files:**
- Modify: none
- Test: `git status`

- [ ] **Step 1: 仅检查 vendor 目录相关状态**

Run:

```bash
cd /c/Users/sai/project/vnpy/.worktrees/xt-first
git status --short -- vendor/vnpy_qmt
```

Expected:

- 在提交前显示 `A` 类新增文件
- 在提交后无输出

- [ ] **Step 2: 抽样检查当前工作树中其它已存在改动未被重写**

Run:

```bash
cd /c/Users/sai/project/vnpy/.worktrees/xt-first
git status --short
```

Expected:

- 仍然能看到之前已有的未提交改动
- 不应出现因为这次 vendor 操作导致的额外误改

- [ ] **Step 3: 清理临时目录**

Run:

```bash
rm -rf /tmp/vnpy_qmt_vendor
```

Expected:

- `/tmp/vnpy_qmt_vendor` 不存在

- [ ] **Step 4: 最终人工验收**

验收点：

- `vendor/vnpy_qmt` 已存在于当前工作树
- 目录中保留上游源码结构
- `.git` 等远程元数据已删除
- 当前项目运行链路尚未接入这份源码
- 后续可以直接在 `vendor/vnpy_qmt` 内进行本地修改和编译

- [ ] **Step 5: 记录执行完成**

说明：

- 这一任务不额外提交
- 最终向用户汇报关键目录、基准 commit、以及“当前只是纳入源码、还未接入运行环境”
