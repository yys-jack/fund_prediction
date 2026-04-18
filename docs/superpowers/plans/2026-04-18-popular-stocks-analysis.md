# 多基金持仓分析 - 热门股票发现功能实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过分析多只基金的持仓数据，统计每只股票被多少只基金持有，找出被最多基金共同持有的前 30 只热门股票。

**Architecture:** 
- 创建 `modules/popular_stocks.py` 模块，包含 `PopularStocksFinder` 类，负责批量获取基金持仓、统计股票热度、获取股票详情
- 创建 `scripts/find_popular_stocks.py` 脚本作为命令行入口
- 使用现有 `core/tiantian_api.py` 中的 `get_stock_codes` 获取持仓股票
- 使用现有 `core/http_client.py` 获取股票行情

**Tech Stack:** Python 3.7+, requests, 天天基金网 API

---

### Task 1: 更新 config.json 添加热门股票分析配置

**Files:**
- Modify: `config.json.example`
- Modify: `config.json`

- [ ] **Step 1: 修改 config.json.example 添加配置**

```json
{
    "fund_code": "161725",
    "fund_codes": ["161725"],
    "institution_fund": {
        "threshold": 30.0,
        "target_count": 100
    },
    "popular_stocks": {
        "fund_codes": ["161725", "000001", "000002"],
        "top_n": 30
    }
}
```

- [ ] **Step 2: 修改 config.json 添加配置**

使用相同结构更新 `config.json`，`fund_codes` 包含至少 10 只用于测试的基金代码。

- [ ] **Step 3: Commit**

```bash
git add config.json config.json.example
git commit -m "feat: add popular_stocks configuration"
```

---

### Task 2: 创建 PopularStocksFinder 核心模块

**Files:**
- Create: `modules/popular_stocks.py`

- [ ] **Step 1: 创建模块骨架和类定义**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热门股票分析模块

通过分析多只基金的持仓数据，统计每只股票被多少只基金持有，
找出被最多基金共同持有的热门股票。
"""

import json
from typing import List, Dict, Optional
from pathlib import Path

from core.tiantian_api import get_stock_codes
from core.http_client import fetch_json, get_session
from core.config import get_output_dir


class PopularStocksFinder:
    """热门股票发现器 - 分析多基金持仓找出高关注度股票"""

    def __init__(self, fund_codes: List[str], top_n: int = 30):
        """
        初始化热门股票发现器

        Args:
            fund_codes: 要分析的基金代码列表
            top_n: 返回前 N 只热门股票
        """
        self.fund_codes = fund_codes
        self.top_n = top_n
        self.stock_count = {}  # 股票代码 -> 持有它的基金数量
        self.fund_holdings = {}  # 基金代码 -> 该基金持有的股票代码列表
        self.stock_details = {}  # 股票代码 -> 股票详细信息

    def fetch_all_holdings(self) -> Dict[str, List[str]]:
        """
        批量获取所有基金的重仓股票

        Returns:
            基金代码到股票代码列表的映射
        """
        for fund_code in self.fund_codes:
            try:
                stocks = get_stock_codes(fund_code)
                stock_list = [s['code'] for s in stocks]
                self.fund_holdings[fund_code] = stock_list
                print(f"已获取基金 {fund_code} 的 {len(stock_list)} 只持仓股票")
            except Exception as e:
                print(f"获取基金 {fund_code} 持仓失败：{e}")
                self.fund_holdings[fund_code] = []
        return self.fund_holdings

    def count_stock_popularity(self) -> Dict[str, int]:
        """
        统计每只股票被多少只基金持有

        Returns:
            股票代码到持有基金数量的映射
        """
        self.stock_count = {}
        for fund_code, stocks in self.fund_holdings.items():
            for stock_code in stocks:
                if stock_code not in self.stock_count:
                    self.stock_count[stock_code] = 0
                self.stock_count[stock_code] += 1
        return self.stock_count

    def get_top_stocks(self) -> List[tuple]:
        """
        获取前 N 只热门股票（按持有基金数量排序）

        Returns:
            (股票代码，持有基金数量) 元组列表
        """
        sorted_stocks = sorted(
            self.stock_count.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_stocks[:self.top_n]

    def fetch_stock_info(self, stock_code: str, market: str = 'SH') -> Optional[Dict]:
        """
        获取单只股票的详细信息

        Args:
            stock_code: 股票代码
            market: 市场标识 ('SH' 或 'SZ')

        Returns:
            股票详细信息字典，失败返回 None
        """
        secid = f"{'1' if market == 'SH' else '0'}.{stock_code}"
        url = "http://push2.eastmoney.com/api/qt/stock/get"
        params = {"fltt": 2, "secid": secid}

        try:
            data = fetch_json(url, params=params)
            if data and data.get('data'):
                s = data['data']
                price = s.get('f43', 0)
                prev_close = s.get('f46', 0)
                change = price - prev_close if prev_close else 0
                change_pct = (change / prev_close * 100) if prev_close else 0

                return {
                    'code': s.get('f57', stock_code),
                    'name': s.get('f58', 'Unknown'),
                    'price': price,
                    'change': change,
                    'change_pct': change_pct,
                    'prev_close': prev_close,
                    'volume': s.get('f47', 0),
                    'turnover': s.get('f48', 0),
                    'market': market,
                }
        except Exception as e:
            print(f"获取股票 {stock_code} 详情失败：{e}")
        return None

    def fetch_top_stocks_details(self) -> List[Dict]:
        """
        获取前 N 只热门股票的详细信息

        Returns:
            包含股票详细信息的列表
        """
        top_stocks = self.get_top_stocks()
        result = []

        for stock_code, count in top_stocks:
            # 默认使用 SH 市场，如果是 SZ 市场股票会在获取时自动处理
            info = self.fetch_stock_info(stock_code)
            if info:
                info['fund_count'] = count  # 持有该股票的基金数量
                result.append(info)
                self.stock_details[stock_code] = info
                print(f"已获取股票 {stock_code} ({info['name']}) 详情，{count} 只基金持有")
            else:
                # 尝试 SZ 市场
                info = self.fetch_stock_info(stock_code, 'SZ')
                if info:
                    info['fund_count'] = count
                    result.append(info)
                    self.stock_details[stock_code] = info
                    print(f"已获取股票 {stock_code} ({info['name']}) 详情 (SZ), {count} 只基金持有")

        return result

    def analyze(self) -> List[Dict]:
        """
        执行完整分析流程

        Returns:
            热门股票详细信息列表
        """
        print(f"开始分析 {len(self.fund_codes)} 只基金的持仓...")
        self.fetch_all_holdings()
        self.count_stock_popularity()
        print(f"共发现 {len(self.stock_count)} 只不同的股票")
        return self.fetch_top_stocks_details()

    def save_to_csv(self, output_path: Optional[str] = None) -> str:
        """
        保存结果到 CSV 文件

        Args:
            output_path: 输出文件路径，默认生成带时间戳的文件名

        Returns:
            保存的文件路径
        """
        import csv
        from datetime import datetime

        if output_path is None:
            output_dir = get_output_dir()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = output_dir / f'popular_stocks_{timestamp}.csv'
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

        if not self.stock_details:
            print("暂无数据可保存")
            return str(output_path)

        fieldnames = ['rank', 'code', 'name', 'price', 'change', 'change_pct', 
                      'fund_count', 'volume', 'turnover', 'market']

        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, stock in enumerate(self.stock_details.values(), 1):
                row = {
                    'rank': i,
                    'code': stock['code'],
                    'name': stock['name'],
                    'price': stock['price'],
                    'change': stock['change'],
                    'change_pct': stock['change_pct'],
                    'fund_count': stock['fund_count'],
                    'volume': stock['volume'],
                    'turnover': stock['turnover'],
                    'market': stock['market'],
                }
                writer.writerow(row)

        print(f"结果已保存到：{output_path}")
        return str(output_path)

    def print_results(self):
        """打印热门股票结果"""
        if not self.stock_details:
            print("暂无股票数据")
            return

        print(f"\n{'='*90}")
        print(f"热门股票分析结果（基于 {len(self.fund_codes)} 只基金）")
        print(f"{'='*90}")
        print(f"{'排名':<6} {'代码':<8} {'名称':<12} {'现价':>10} {'涨跌额':>8} {'涨幅%':>8} {'基金数':>8} {'成交量 (手)':>12}")
        print(f"{'='*90}")

        for i, stock in enumerate(self.stock_details.values(), 1):
            print(f"{i:<6} {stock['code']:<8} {stock['name']:<12} "
                  f"{stock['price']:>10.2f} {stock['change']:>8.2f} "
                  f"{stock['change_pct']:>8.2f} {stock['fund_count']:>8} "
                  f"{stock['volume']:>12.0f}")

        print(f"{'='*90}")
```

- [ ] **Step 2: Commit**

```bash
git add modules/popular_stocks.py
git commit -m "feat: add PopularStocksFinder module for multi-fund holdings analysis"
```

---

### Task 3: 创建命令行脚本

**Files:**
- Create: `scripts/find_popular_stocks.py`

- [ ] **Step 1: 创建命令行入口脚本**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热门股票分析脚本

分析多只基金的持仓数据，找出被最多基金共同持有的热门股票。

使用方法:
    python scripts/find_popular_stocks.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import load_config, get_output_dir
from modules.popular_stocks import PopularStocksFinder


def main():
    """主函数"""
    # 加载配置
    config = load_config()
    
    # 获取热门股票分析配置
    popular_stocks_config = config.get('popular_stocks', {})
    fund_codes = popular_stocks_config.get('fund_codes', config.get('fund_codes', ['161725']))
    top_n = popular_stocks_config.get('top_n', 30)

    print(f"配置基金数量：{len(fund_codes)}")
    print(f"目标热门股票数量：{top_n}")
    print("-" * 50)

    # 创建分析器并运行
    finder = PopularStocksFinder(fund_codes=fund_codes, top_n=top_n)
    results = finder.analyze()

    if not results:
        print("未找到任何股票数据")
        return 1

    # 打印结果
    finder.print_results()

    # 保存到 CSV
    output_dir = get_output_dir()
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_path = output_dir / f'popular_stocks_{timestamp}.csv'
    finder.save_to_csv(str(output_path))

    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Commit**

```bash
git add scripts/find_popular_stocks.py
git commit -m "feat: add find_popular_stocks.py command-line script"
```

---

### Task 4: 更新 README.md 添加功能说明

**Files:**
- Modify: `README.md`

- [ ] **Step 1: 更新项目结构**

在 `scripts/` 部分添加新脚本说明：

```markdown
├── scripts/                  # 命令行脚本
│   ├── fetch_performance.py  # 业绩分析入口
│   ├── fetch_holdings.py     # 持仓分析入口
│   ├── find_institutions.py  # 机构分析入口
│   └── find_popular_stocks.py # 热门股票分析入口
```

- [ ] **Step 2: 在快速开始部分添加使用说明**

在 "3. 运行脚本" 部分添加：

```bash
# 热门股票分析（多基金持仓统计）
python scripts/find_popular_stocks.py
```

- [ ] **Step 3: 添加新功能详细说明**

在 "功能模块" 章节末尾添加：

```markdown
### 5. 热门股票分析 (`modules/popular_stocks.py`)

通过分析多只基金的持仓数据，统计每只股票被多少只基金持有，
找出被最多基金共同持有的热门股票（高关注度股票）。

**配置：**

在 `config.json` 中添加：

```json
{
    "popular_stocks": {
        "fund_codes": ["161725", "000001", "000002"],
        "top_n": 30
    }
}
```

**使用示例：**

```python
from modules.popular_stocks import PopularStocksFinder

# 分析 10 只基金的持仓
fund_codes = ["161725", "000001", "000002", "..."]
finder = PopularStocksFinder(fund_codes=fund_codes, top_n=30)
results = finder.analyze()
finder.print_results()
finder.save_to_csv('output/popular_stocks.csv')
```

**输出：**
- 终端打印热门股票列表，按持有基金数量降序排列
- CSV 文件：`output/popular_stocks_{timestamp}.csv`

**输出字段：**
- `rank`: 排名
- `code`: 股票代码
- `name`: 股票名称
- `price`: 现价
- `change`: 涨跌额
- `change_pct`: 涨幅%
- `fund_count`: 持有该股票的基金数量
- `volume`: 成交量
- `turnover`: 成交额
- `market`: 市场标识（SH/SZ）
```

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: add popular_stocks feature documentation"
```

---

### Task 5: 创建测试文件

**Files:**
- Create: `tests/test_popular_stocks.py`

- [ ] **Step 1: 创建测试文件**

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
热门股票分析模块测试
"""

import pytest
from modules.popular_stocks import PopularStocksFinder


class TestPopularStocksFinder:
    """PopularStocksFinder 测试类"""

    def test_init(self):
        """测试初始化"""
        fund_codes = ["161725", "000001", "000002"]
        finder = PopularStocksFinder(fund_codes, top_n=30)
        
        assert finder.fund_codes == fund_codes
        assert finder.top_n == 30
        assert finder.stock_count == {}
        assert finder.fund_holdings == {}

    def test_count_stock_popularity(self):
        """测试股票热度统计"""
        finder = PopularStocksFinder(["000001", "000002", "000003"], top_n=10)
        
        # 模拟持仓数据
        finder.fund_holdings = {
            "000001": ["600519", "000858", "000333"],
            "000002": ["600519", "000858", "300750"],
            "000003": ["600519", "000333", "300750"],
        }
        
        result = finder.count_stock_popularity()
        
        # 600519 被 3 只基金持有，应该排在第一位
        assert result["600519"] == 3
        assert result["000858"] == 2
        assert result["000333"] == 2
        assert result["300750"] == 2

    def test_get_top_stocks(self):
        """测试获取前 N 只热门股票"""
        finder = PopularStocksFinder(["000001", "000002"], top_n=2)
        finder.stock_count = {
            "600519": 3,
            "000858": 2,
            "000333": 1,
        }
        
        top = finder.get_top_stocks()
        
        assert len(top) == 2
        assert top[0] == ("600519", 3)
        assert top[1] == ("000858", 2)

    def test_get_top_stocks_limit(self):
        """测试 top_n 限制"""
        finder = PopularStocksFinder(["000001"], top_n=5)
        finder.stock_count = {
            "stock1": 5,
            "stock2": 4,
            "stock3": 3,
            "stock4": 2,
            "stock5": 1,
            "stock6": 1,
            "stock7": 1,
        }
        
        top = finder.get_top_stocks()
        
        assert len(top) == 5

    def test_fetch_stock_info_format(self):
        """测试股票信息获取（仅验证格式，不验证实际数据）"""
        finder = PopularStocksFinder(["161725"], top_n=10)
        
        # 测试是否能返回正确格式的数据
        info = finder.fetch_stock_info("600519")
        
        if info:  # 如果 API 可用
            assert 'code' in info
            assert 'name' in info
            assert 'price' in info
            assert 'change_pct' in info
            assert 'market' in info


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

- [ ] **Step 2: Commit**

```bash
git add tests/test_popular_stocks.py
git commit -m "test: add tests for PopularStocksFinder"
```

---

### Task 6: 运行测试和验证

**Files:**
- N/A (验证任务)

- [ ] **Step 1: 运行单元测试**

```bash
cd /home/yy/workspace/fund_prediction
python -m pytest tests/test_popular_stocks.py -v
```

预期：所有测试通过（除依赖外部 API 的测试可能因网络问题失败）

- [ ] **Step 2: 运行脚本验证功能**

```bash
python scripts/find_popular_stocks.py
```

预期：
- 成功获取至少 10 只基金的持仓数据
- 统计出多只股票并按基金持有数量排序
- 打印前 30 只热门股票
- 生成 CSV 文件

- [ ] **Step 3: 验证 CSV 输出**

```bash
ls -la output/popular_stocks_*.csv
head -5 output/popular_stocks_*.csv
```

预期：
- CSV 文件存在
- 包含正确的表头：rank, code, name, price, change, change_pct, fund_count, volume, turnover, market
- 数据按 fund_count 降序排列

- [ ] **Step 4: Commit（如有修改）**

```bash
git add .
git commit -m "fix: address issues found in testing"
```

---

## 完成标准

所有任务完成后：
1. `modules/popular_stocks.py` 包含完整的 `PopularStocksFinder` 类
2. `scripts/find_popular_stocks.py` 可独立运行
3. `config.json` 和 `config.json.example` 包含 `popular_stocks` 配置
4. `README.md` 包含新功能的使用说明
5. `tests/test_popular_stocks.py` 测试通过
6. 脚本运行能生成正确的 CSV 输出

## 注意事项

1. **API 调用频率**: 批量获取数据时注意不要过于频繁，可能需要添加延时
2. **错误处理**: 单只基金获取失败不应影响其他基金的分析
3. **数据一致性**: 确保股票代码格式统一（不带市场前缀）
4. **UTF-8 编码**: CSV 输出使用 `utf-8-sig` 编码以支持 Excel 打开
