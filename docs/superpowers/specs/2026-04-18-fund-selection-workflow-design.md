# 基金筛选流程设计文档

**日期**: 2026-04-18  
**状态**: 已批准

---

## 需求概述

构建一个自动化流程，完成以下任务：
1. 获取 50 只机构持有基金（机构占比≥30%）
2. 获取 50 只高收益基金（近 1 年收益率≥30%）
3. 合并去重得到基金池（约 100 只）
4. 分析基金池中基金的重仓股票，找出前 50 只热门股票

**约束条件**：
- 步骤 1 和 2 并行执行，合并输出
- 收益率阈值 30% 为临时覆盖（不修改配置）
- 输出包含完整元数据（代码、名称、来源、收益率、机构占比、规模）

---

## 架构设计

### 流程图

```
┌─────────────────────────────────────────────────────────────┐
│  主流程脚本：scripts/fund_selection_workflow.py              │
├─────────────────────────────────────────────────────────────┤
│  步骤 1: 双路并行获取基金池                                   │
│    ├─ 机构持有基金 (50 只，占比≥30%)                           │
│    └─ 高收益基金 (50 只，近 1 年≥30%)                          │
│         ↓ 合并去重                                            │
│    → 输出：output/fund_pool_{timestamp}.csv                  │
│      字段：基金代码，基金名称，来源标签，收益率，机构占比，基金规模  │
│                                                             │
│  步骤 2: 热门股票分析                                         │
│    ├─ 读取 fund_pool.csv                                     │
│    ├─ 提取所有基金代码                                        │
│    ├─ 分析重仓股票分布                                        │
│    └─ 输出前 50 只热门股票                                      │
│    → 输出：output/popular_stocks_{timestamp}.csv             │
└─────────────────────────────────────────────────────────────┘
```

### 模块复用

| 功能 | 现有模块 | 调整 |
|------|---------|------|
| 机构持有基金 | `modules/institution_analysis.py` | 无 |
| 高收益基金 | `modules/high_return_funds.py` | 支持收益率阈值参数 |
| 热门股票 | `modules/popular_stocks.py` | 支持从 CSV 读取基金池 |
| 主流程 | 新建 | `scripts/fund_selection_workflow.py` |

---

## 数据结构

### fund_pool_{timestamp}.csv

| 字段 | 类型 | 说明 |
|------|------|------|
| 基金代码 | string | 基金唯一标识 |
| 基金名称 | string | 基金全称 |
| 来源标签 | string | "机构" / "高收益" / "重复" |
| 近 1 年收益率 | string | 百分比数据 (如 "35.2%") |
| 机构持有占比 | string | 百分比数据 (如 "45.3%")，高收益基金可能为 N/A |
| 基金规模 (亿元) | string | 规模数据 |

### popular_stocks_{timestamp}.csv

| 字段 | 类型 | 说明 |
|------|------|------|
| 序号 | int | 排名 |
| 股票代码 | string | 股票唯一标识 |
| 股票名称 | string | 股票全称 |
| 现价 | float | 当前价格 |
| 涨幅% | float | 日涨幅 |
| 持有基金数 | int | 被多少只基金持有 |
| 持有基金列表 | string | 持有该基金的代码列表 (逗号分隔) |

---

## 执行流程

### 步骤 1: 获取基金池

```python
# 并行执行
institutions = search_institution_funds(threshold=30.0, target_count=50)
high_returns = find_high_return_funds(min_return=30.0, target_count=50)

# 合并去重
fund_pool = merge_and_dedup(institutions, high_returns)

# 保存
save_to_csv(fund_pool, f"output/fund_pool_{timestamp}.csv")
```

### 步骤 2: 热门股票分析

```python
# 读取基金池
fund_codes = load_fund_codes(f"output/fund_pool_{timestamp}.csv")

# 分析热门股票
finder = PopularStocksFinder(fund_codes, top_count=50)
finder.analyze()
finder.to_csv(f"output/popular_stocks_{timestamp}.csv")
```

---

## 命令行接口

```bash
# 一键执行完整流程
python scripts/fund_selection_workflow.py

# 可选：只执行步骤 1
python scripts/fund_selection_workflow.py --step 1

# 可选：只执行步骤 2 (需指定基金池文件)
python scripts/fund_selection_workflow.py --step 2 --fund-pool output/fund_pool_xxx.csv

# 可选：自定义热门股票数量
python scripts/fund_selection_workflow.py --top-stocks 30
```

---

## 输出示例

```
[步骤 1/2] 获取机构持有基金... 完成 (50 只)
[步骤 1/2] 获取高收益基金 (≥30%)... 完成 (50 只)
[步骤 1/2] 合并去重... 完成 (共 98 只，去重 2 只)
→ 已保存：output/fund_pool_20260418_143022.csv

[步骤 2/2] 分析热门股票...
→ 已保存：output/popular_stocks_20260418_143055.csv
```

---

## 测试计划

1. 验证机构持有基金筛选逻辑
2. 验证高收益基金筛选逻辑 (30% 阈值)
3. 验证合并去重逻辑
4. 验证热门股票分析逻辑
5. 验证 CSV 输出格式

---

## 待办事项

- [ ] 修改 `modules/high_return_funds.py` 支持收益率阈值参数
- [ ] 修改 `modules/popular_stocks.py` 支持从 CSV 读取基金池
- [ ] 创建 `scripts/fund_selection_workflow.py` 主流程脚本
- [ ] 添加命令行参数解析
- [ ] 测试完整流程
