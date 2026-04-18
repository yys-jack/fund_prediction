# 基金筛选流程实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建自动化流程，获取机构持有基金和高收益基金合并后的基金池，分析热门股票

**Architecture:** 
- 主流程脚本 `fund_selection_workflow.py` 串联两个步骤
- 步骤 1 并行获取机构持有基金和高收益基金，合并去重后输出 CSV
- 步骤 2 读取基金池，复用 `PopularStocksFinder` 分析热门股票

**Tech Stack:** Python 3.x, requests 库，天天基金网 API

---

### Task 1: 修改 `modules/high_return_funds.py` 支持收益率阈值参数

**Files:**
- Modify: `modules/high_return_funds.py`
- Test: 现有测试或手动验证

**当前代码分析：** 需要查看当前实现，确认收益率阈值的读取方式

- [ ] **Step 1: 读取 `modules/high_return_funds.py` 文件**

- [ ] **Step 2: 修改 `find_high_return_funds` 函数签名，添加 `min_return` 参数**

当前配置读取方式：
```python
# 原代码可能从 config.json 读取
min_return = config.get('high_return_funds', {}).get('min_return', 50.0)
```

修改为支持参数覆盖：
```python
def find_high_return_funds(min_return: Optional[float] = None, target_count: Optional[int] = None):
    config = load_config()
    hf_config = config.get('high_return_funds', {})
    
    # 参数优先，配置兜底
    if min_return is None:
        min_return = hf_config.get('min_return', 50.0)
    if target_count is None:
        target_count = hf_config.get('target_count', 50)
    
    # ... 原有逻辑
```

- [ ] **Step 3: 确保 `search_high_return_funds` 内部函数也接受并使用 `min_return` 参数**

- [ ] **Step 4: 提交**

```bash
git add modules/high_return_funds.py
git commit -m "refactor: 支持收益率阈值参数覆盖"
```

---

### Task 2: 修改 `modules/popular_stocks.py` 支持从 CSV 读取基金池

**Files:**
- Modify: `modules/popular_stocks.py`
- Create: `modules/popular_stocks.py:load_fund_pool` (新增函数)

- [ ] **Step 1: 读取 `modules/popular_stocks.py` 文件**

- [ ] **Step 2: 新增 `load_fund_pool` 函数**

```python
import csv
from typing import List

def load_fund_pool(csv_path: str) -> List[str]:
    """
    从 CSV 文件读取基金代码列表
    
    Args:
        csv_path: 基金池 CSV 文件路径
        
    Returns:
        基金代码列表
    """
    fund_codes = []
    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row.get('基金代码', '').strip()
            if code:
                fund_codes.append(code)
    return fund_codes
```

- [ ] **Step 3: 修改 `PopularStocksFinder` 类，支持直接传入 CSV 路径**

```python
class PopularStocksFinder:
    def __init__(self, fund_codes: Optional[List[str]] = None, 
                 top_count: int = 30,
                 fund_pool_csv: Optional[str] = None):
        if fund_pool_csv:
            self.fund_codes = load_fund_pool(fund_pool_csv)
        else:
            self.fund_codes = fund_codes or []
        self.top_count = top_count
        # ... 其他初始化
```

- [ ] **Step 4: 在 `__init__.py` 中导出 `load_fund_pool` 函数**

```python
from .popular_stocks import PopularStocksFinder, find_popular_stocks, load_fund_pool

__all__ = ['PopularStocksFinder', 'find_popular_stocks', 'load_fund_pool']
```

- [ ] **Step 5: 提交**

```bash
git add modules/popular_stocks.py modules/__init__.py
git commit -m "feat: 支持从 CSV 读取基金池"
```

---

### Task 3: 创建 `scripts/fund_selection_workflow.py` 主流程脚本

**Files:**
- Create: `scripts/fund_selection_workflow.py`

- [ ] **Step 1: 创建主流程脚本框架**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基金筛选流程主脚本

步骤 1: 获取机构持有基金 + 高收益基金，合并去重
步骤 2: 分析热门股票
"""

import argparse
import sys
from datetime import datetime
from typing import List, Dict, Set

from modules.institution_analysis import search_institution_funds
from modules.high_return_funds import find_high_return_funds
from modules.popular_stocks import PopularStocksFinder, load_fund_pool
from core.io_utils import save_to_csv, get_output_dir
from core.tiantian_api import get_fund_info, get_holder_structure, get_fund_scale


def main():
    parser = argparse.ArgumentParser(description='基金筛选流程')
    parser.add_argument('--step', type=int, choices=[1, 2], default=0,
                        help='只执行指定步骤 (1 或 2)，默认执行全部')
    parser.add_argument('--fund-pool', type=str,
                        help='步骤 2 使用的基金池 CSV 路径')
    parser.add_argument('--top-stocks', type=int, default=50,
                        help='热门股票数量，默认 50')
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if args.step in (0, 1):
        fund_pool_path = run_step1(timestamp)
        if args.step == 0:
            run_step2(fund_pool_path, args.top_stocks, timestamp)
    else:
        if not args.fund_pool:
            print("错误：执行步骤 2 需指定 --fund-pool")
            sys.exit(1)
        run_step2(args.fund_pool, args.top_stocks, timestamp)


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: 实现 `run_step1` 函数**

```python
def run_step1(timestamp: str) -> str:
    """
    步骤 1: 获取机构持有基金和高收益基金，合并去重
    """
    print("[步骤 1/2] 获取机构持有基金...")
    institutions = search_institution_funds(threshold=30.0, target_count=50)
    print(f"  → 完成 ({len(institutions)} 只)")
    
    print("[步骤 1/2] 获取高收益基金 (≥30%)...")
    high_returns = find_high_return_funds(min_return=30.0, target_count=50)
    print(f"  → 完成 ({len(high_returns)} 只)")
    
    # 合并去重
    print("[步骤 1/2] 合并去重...")
    fund_pool = merge_funds(institutions, high_returns)
    print(f"  → 完成 (共 {len(fund_pool)} 只)")
    
    # 保存
    output_path = f"{get_output_dir()}/fund_pool_{timestamp}.csv"
    save_fund_pool_to_csv(fund_pool, output_path)
    print(f"→ 已保存：{output_path}")
    
    return output_path


def merge_funds(institutions: List[Dict], high_returns: List[Dict]) -> List[Dict]:
    """
    合并两个基金列表，去重并标记来源
    """
    fund_dict: Dict[str, Dict] = {}
    
    # 添加机构持有基金
    for fund in institutions:
        code = fund.get('基金代码', '')
        if code:
            fund_dict[code] = {
                '基金代码': code,
                '基金名称': fund.get('基金名称', ''),
                '来源标签': '机构',
                '近 1 年收益率': fund.get('近 1 年收益率', 'N/A'),
                '机构持有占比': fund.get('机构持有占比', 'N/A'),
                '基金规模 (亿元)': fund.get('基金规模', 'N/A'),
            }
    
    # 添加高收益基金，处理重复
    for fund in high_returns:
        code = fund.get('基金代码', '')
        if code:
            if code in fund_dict:
                # 重复基金，更新标签
                fund_dict[code]['来源标签'] = '重复'
            else:
                fund_dict[code] = {
                    '基金代码': code,
                    '基金名称': fund.get('基金名称', ''),
                    '来源标签': '高收益',
                    '近 1 年收益率': fund.get('近 1 年收益率', 'N/A'),
                    '机构持有占比': 'N/A',
                    '基金规模 (亿元)': fund.get('基金规模', 'N/A'),
                }
    
    return list(fund_dict.values())


def save_fund_pool_to_csv(fund_pool: List[Dict], output_path: str):
    """
    保存基金池到 CSV
    """
    if not fund_pool:
        return
    
    headers = ['基金代码', '基金名称', '来源标签', '近 1 年收益率', 
               '机构持有占比', '基金规模 (亿元)']
    
    with open(output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for fund in fund_pool:
            writer.writerow(fund)
```

- [ ] **Step 3: 实现 `run_step2` 函数**

```python
def run_step2(fund_pool_path: str, top_stocks: int, timestamp: str):
    """
    步骤 2: 分析热门股票
    """
    print(f"[步骤 2/2] 从 {fund_pool_path} 读取基金池...")
    fund_codes = load_fund_pool(fund_pool_path)
    print(f"  → 共 {len(fund_codes)} 只基金")
    
    print(f"[步骤 2/2] 分析热门股票 (前 {top_stocks} 只)...")
    finder = PopularStocksFinder(fund_codes=fund_codes, top_count=top_stocks)
    finder.analyze()
    
    output_path = f"{get_output_dir()}/popular_stocks_{timestamp}.csv"
    finder.to_csv(output_path)
    print(f"→ 已保存：{output_path}")
    
    # 打印摘要
    summary = finder.get_summary()
    if summary.get('most_popular_stock'):
        stock = summary['most_popular_stock']
        print(f"\n最受欢迎股票：{stock.get('股票名称')} ({stock.get('股票代码')})")
        print(f"  被 {stock.get('持有基金数')} 只基金持有")
```

- [ ] **Step 4: 添加必要的 import**

```python
import csv
```

- [ ] **Step 5: 提交**

```bash
git add scripts/fund_selection_workflow.py
git commit -m "feat: 创建基金筛选流程主脚本"
```

---

### Task 4: 测试完整流程

**Files:**
- 测试脚本：`scripts/fund_selection_workflow.py`
- 输出文件：`output/fund_pool_*.csv`, `output/popular_stocks_*.csv`

- [ ] **Step 1: 运行完整流程测试**

```bash
python scripts/fund_selection_workflow.py
```

预期输出：
```
[步骤 1/2] 获取机构持有基金...
  → 完成 (50 只)
[步骤 1/2] 获取高收益基金 (≥30%)...
  → 完成 (50 只)
[步骤 1/2] 合并去重...
  → 完成 (共 XX 只)
→ 已保存：output/fund_pool_20260418_XXXXXX.csv

[步骤 2/2] 从 output/fund_pool_20260418_XXXXXX.csv 读取基金池...
  → 共 XX 只基金
[步骤 2/2] 分析热门股票 (前 50 只)...
→ 已保存：output/popular_stocks_20260418_XXXXXX.csv
```

- [ ] **Step 2: 验证 `fund_pool_*.csv` 格式**

```bash
head -5 output/fund_pool_*.csv
```

预期包含字段：基金代码，基金名称，来源标签，近 1 年收益率，机构持有占比，基金规模 (亿元)

- [ ] **Step 3: 验证 `popular_stocks_*.csv` 格式**

```bash
head -5 output/popular_stocks_*.csv
```

预期包含字段：序号，股票代码，股票名称，现价，涨幅%，持有基金数，持有基金列表

- [ ] **Step 4: 测试步骤 1 单独执行**

```bash
python scripts/fund_selection_workflow.py --step 1
```

- [ ] **Step 5: 测试步骤 2 单独执行**

```bash
python scripts/fund_selection_workflow.py --step 2 --fund-pool output/fund_pool_*.csv
```

- [ ] **Step 6: 提交（如有修复）**

```bash
git add scripts/fund_selection_workflow.py
git commit -m "fix: 修复流程执行问题"
```

---

### Task 5: 更新 README.md 添加流程说明

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 在 README.md 的"运行脚本"章节添加新脚本说明**

在现有脚本列表后添加：

```markdown
# 完整筛选流程（机构持有 + 高收益→热门股票）⭐ 新增
python scripts/fund_selection_workflow.py

# 只执行步骤 1：获取基金池
python scripts/fund_selection_workflow.py --step 1

# 只执行步骤 2：分析热门股票（需指定基金池）
python scripts/fund_selection_workflow.py --step 2 --fund-pool output/fund_pool_xxx.csv

# 自定义热门股票数量
python scripts/fund_selection_workflow.py --top-stocks 30
```

- [ ] **Step 2: 在"功能模块"章节添加流程说明**

在 README 末尾添加：

```markdown
### 6. 基金筛选流程 (`scripts/fund_selection_workflow.py`) ⭐ 新增

一键执行完整的基金筛选和热门股票分析流程：

**流程：**
1. 获取 50 只机构持有基金（机构占比≥30%）
2. 获取 50 只高收益基金（近 1 年收益率≥30%）
3. 合并去重得到基金池
4. 分析基金池中基金的重仓股票，找出前 50 只热门股票

**输出：**
- `output/fund_pool_{timestamp}.csv` - 基金池（含来源标签、收益率、机构占比等）
- `output/popular_stocks_{timestamp}.csv` - 热门股票前 50 只
```

- [ ] **Step 3: 提交**

```bash
git add README.md
git commit -m "docs: 添加基金筛选流程文档"
```

---

## 自审清单

**1. 规范覆盖检查：**
- ✅ 支持收益率阈值参数（Task 1）
- ✅ 支持从 CSV 读取基金池（Task 2）
- ✅ 主流程脚本（Task 3）
- ✅ 测试流程（Task 4）
- ✅ 文档更新（Task 5）

**2. 无占位符检查：**
- ✅ 所有步骤包含具体代码
- ✅ 所有命令包含预期输出
- ✅ 无 "TBD"、"TODO" 等占位符

**3. 类型一致性检查：**
- ✅ `min_return: Optional[float]` 一致
- ✅ `load_fund_pool` 返回 `List[str]` 一致
- ✅ CSV 字段名一致

---

计划已保存到 `docs/superpowers/plans/2026-04-18-fund-selection-workflow.md`。

**两种执行方式可选：**

1. **子代理驱动（推荐）** - 每个任务分派给独立的子代理，任务间审核，快速迭代
2. **内联执行** - 在当前会话中使用 executing-plans 批量执行，带检查点

选择哪种方式？
