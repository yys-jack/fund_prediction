# Fund Prediction - 基金数据分析工具

一个基于 Python 的基金数据分析工具，使用天天基金网 API 获取基金数据，支持基金持有人结构分析、收益走势分析和重仓股分析。

## 项目结构

```
fund_prediction/
├── core/                     # 核心模块
│   ├── __init__.py           # 模块导出
│   ├── config.py             # 配置管理
│   ├── http_client.py        # HTTP 客户端
│   ├── tiantian_api.py       # 天天基金 API 封装
│   └── io_utils.py           # 输入输出工具
├── modules/                  # 功能模块
│   ├── __init__.py
│   ├── fund_holdings.py      # 基金持仓分析
│   ├── fund_performance.py   # 基金业绩分析
│   ├── institution_analysis.py # 机构持有分析
│   ├── popular_stocks.py     # 热门股票分析 ⭐ 新增
│   ├── high_return_funds.py  # 高收益基金筛选 ⭐ 新增
│   ├── dingtalk_notifier.py  # 钉钉通知
│   └── dingtalk_bot/         # 钉钉配置目录
│       ├── config.json       # 钉钉配置（不提交）
│       └── config.json.example
├── scripts/                  # 命令行脚本
│   ├── fetch_performance.py  # 业绩分析入口
│   ├── fetch_holdings.py     # 持仓分析入口
│   ├── find_institutions.py  # 机构分析入口
│   ├── find_popular_stocks.py # 热门股票分析入口 ⭐ 新增
│   └── find_high_return_funds.py # 高收益基金筛选 ⭐ 新增
├── tests/                    # 测试目录
│   └── test_core.py          # 核心模块测试
├── config.json               # 全局配置文件
├── config.json.example       # 配置模板
├── output/                   # 数据输出目录
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 配置基金代码

编辑 `config.json` 文件：

```json
{
    "fund_code": "161725",
    "fund_codes": ["161725"],
    "institution_fund": {
        "threshold": 30.0,
        "target_count": 100
    }
}
```

**配置项说明：**
- `fund_code`: 默认基金代码，用于所有单基金分析
- `fund_codes`: 基金代码列表，用于批量分析
- `institution_fund.threshold`: 机构持有占比阈值（%）
- `institution_fund.target_count`: 目标找到符合条件的基金数量
- `popular_stocks.fund_codes`: 用于热门股票分析的基金代码列表 ⭐ 新增
- `popular_stocks.top_count`: 返回的热门股票数量，默认 30 ⭐ 新增
- `high_return_funds.min_return`: 最低收益率阈值（%），默认 50 ⭐ 新增
- `high_return_funds.target_count`: 目标找到数量，默认 50 ⭐ 新增

### 3. 运行脚本

```bash
# 获取基金业绩走势
python scripts/fetch_performance.py

# 获取基金持仓股票
python scripts/fetch_holdings.py

# 筛选机构持有基金
python scripts/find_institutions.py

# 分析热门股票（被多只基金共同持有） ⭐ 新增
python scripts/find_popular_stocks.py

# 筛选高收益股票型基金（近 1 年收益>50%） ⭐ 新增
python scripts/find_high_return_funds.py

# 完整筛选流程（机构持有 + 高收益→热门股票）⭐ 新增
python scripts/fund_selection_workflow.py

# 只执行步骤 1：获取基金池
python scripts/fund_selection_workflow.py --step 1

# 只执行步骤 2：分析热门股票（需指定基金池）
python scripts/fund_selection_workflow.py --step 2 --fund-pool output/fund_pool_xxx.csv

# 自定义热门股票数量
python scripts/fund_selection_workflow.py --top-stocks 30
```

## 功能模块

### 1. 基金业绩分析 (`modules/fund_performance.py`)

获取基金近 1 年收益走势数据，包括：
- 单位净值、累计净值
- 日增长率、累计收益率

**使用示例：**
```python
from modules.fund_performance import fetch_fund_performance, save_performance_to_csv

data = fetch_fund_performance('161725')
save_performance_to_csv(data, '161725')
```

**输出：** `output/fund_{code}_1year.csv`

### 2. 基金持仓分析 (`modules/fund_holdings.py`)

获取基金的重仓股票和实时行情：

**使用示例：**
```python
from modules.fund_holdings import FundHoldingsFetcher

fetcher = FundHoldingsFetcher('161725')
fetcher.fetch_fund_data()
fetcher.fetch_stock_details()
fetcher.print_holdings()
```

**输出：** 终端打印 + `fund_{code}_holdings.json`

### 3. 机构持有分析 (`modules/institution_analysis.py`)

筛选机构持有占比高于指定阈值的基金：

**使用示例：**
```python
from modules.institution_analysis import search_institution_funds, save_institution_funds

result = search_institution_funds(threshold=30.0, target_count=100)
save_institution_funds(result)
```

**输出：** `output/institution_funds_{timestamp}.csv`

### 4. 热门股票分析 (`modules/popular_stocks.py`) ⭐ 新增

通过分析多只基金的持仓数据，找出被最多基金共同持有的热门股票：
- 批量获取多只基金的重仓股票代码
- 统计每只股票被多少只基金持有
- 按持有基金数量排序，找出前 N 只热门股票
- 获取股票实时行情（价格、涨幅等）

**使用示例：**
```python
from modules.popular_stocks import PopularStocksFinder, find_popular_stocks

# 方法 1：便捷函数
fund_codes = ['161725', '000083', '110011', '000363']
find_popular_stocks(fund_codes, top_count=30)

# 方法 2：使用类（更灵活）
finder = PopularStocksFinder(fund_codes, top_count=30)
finder.analyze()
finder.print_results()
finder.to_csv()  # 保存 CSV

# 获取摘要信息
summary = finder.get_summary()
print(f"最受欢迎股票：{summary['most_popular_stock']['股票名称']}")
```

**输出：** 
- 终端打印热门股票列表
- `output/popular_stocks_{timestamp}.csv`

**输出示例：**

| 序号 | 股票代码 | 股票名称 | 现价 | 涨幅% | 持有基金数 | 持有基金 |
|------|---------|---------|------|------|-----------|---------|
| 1 | 600519 | 贵州茅台 | 1407.24 | 0.52 | 3 | 161725,000083,110011 |
| 2 | 000568 | 泸州老窖 | 101.20 | 0.20 | 3 | 161725,000083,110011 |
| 3 | 600809 | 山西汾酒 | 139.50 | 0.22 | 2 | 161725,110011 |

### 5. 钉钉通知 (`modules/dingtalk_notifier.py`)

发送消息到钉钉群聊：

**配置：**
```bash
cp modules/dingtalk_bot/config.json.example modules/dingtalk_bot/config.json
# 编辑 config.json 填入 access_token 和 secret
```

**使用示例：**
```python
from modules.dingtalk_notifier import DingTalkBot, load_dingtalk_config

config = load_dingtalk_config()
bot = DingTalkBot(config['access_token'], config.get('secret'))
bot.send_text("基金数据更新完成！")
```

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

**使用示例：**
```python
# 一键执行完整流程
python scripts/fund_selection_workflow.py

# 只执行步骤 1：获取基金池
python scripts/fund_selection_workflow.py --step 1

# 只执行步骤 2：分析热门股票（需指定基金池）
python scripts/fund_selection_workflow.py --step 2 --fund-pool output/fund_pool_xxx.csv

# 自定义热门股票数量
python scripts/fund_selection_workflow.py --top-stocks 30
```

## 核心 API

### 配置管理 (`core.config`)

```python
from core import load_config, get_fund_code, get_output_dir

config = load_config()      # 加载完整配置
fund_code = get_fund_code() # 获取默认基金代码
output_dir = get_output_dir() # 获取输出目录
```

### 天天基金 API (`core.tiantian_api`)

```python
from core.tiantian_api import (
    get_fund_info,        # 获取基金信息
    get_fund_list,        # 获取基金列表
    get_holder_structure, # 获取持有人结构
    get_fund_scale,       # 获取基金规模
    get_historical_nav,   # 获取历史净值
)
```

### HTTP 客户端 (`core.http_client`)

```python
from core.http_client import fetch_text, fetch_json, get_session

content = fetch_text(url)           # 获取文本
data = fetch_json(url, params={})   # 获取 JSON
session = get_session()             # 创建 Session
```

### 文件操作 (`core.io_utils`)

```python
from core.io_utils import save_to_csv, save_to_json, setup_utf8_stdout

save_to_csv(data, 'output.csv')     # 保存 CSV
save_to_json(data, 'output.json')   # 保存 JSON
setup_utf8_stdout()                 # 设置 UTF-8 输出
```

## 运行测试

```bash
cd /path/to/fund_prediction
python -m pytest tests/
# 或
python tests/test_core.py
```

## 数据源

所有数据来自 [天天基金网](http://fund.eastmoney.com/)

主要 API：
- `https://fund.eastmoney.com/pingzhongdata/{fund_code}.js` - 基金详情
- `https://fund.eastmoney.com/js/fundcode_search.js` - 基金列表
- `http://api.fund.eastmoney.com/f10/lsjz` - 历史净值
- `http://push2.eastmoney.com/api/qt/stock/get` - 股票行情

## 输出示例

### 基金业绩走势 CSV

| 日期 | 单位净值 | 累计净值 | 日增长率 (%) | 累计收益率 (%) |
|-----|---------|---------|------------|--------------|
| 2025-04-21 | 0.8108 | 2.5269 | 0.52 | 0.00 |
| 2025-04-22 | 0.8156 | 2.5418 | 0.59 | 0.59 |

### 机构持有基金 CSV

| 基金代码 | 基金名称 | 机构持有占比 (%) | 个人持有占比 (%) | 基金规模 (亿元) |
|---------|---------|----------------|----------------|---------------|
| 000116 | JSFYCZDQZQA | 99.14 | 0.86 | 44.32 |

## License

MIT License
