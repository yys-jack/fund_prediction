# Fund Prediction - 基金数据分析工具

一个基于 Python 的基金数据分析工具，使用天天基金网 API 获取基金数据，支持基金持有人结构分析和收益走势分析。

## 项目结构

```
fund_prediction/
├── fetch_fund_data/          # 基金数据获取模块
│   └── fetch_fund_data.py    # 获取基金近 1 年收益走势
├── institution_funds/        # 机构持有基金分析模块
│   └── find_institution_funds.py  # 查找机构持有占比高的基金
├── output/                   # 数据输出目录
└── README.md
```

## 功能模块

### 1. 基金收益走势分析 (`fetch_fund_data.py`)

获取指定基金的近 1 年收益走势数据，包括：
- 单位净值
- 累计净值
- 日增长率
- 累计收益率

**使用方法：**
```python
# 修改基金代码后运行
fund_code = "161725"  # 招商中证白酒指数
```

**输出：** `output/fund_{code}_1year.csv`

### 2. 机构持有基金筛选 (`find_institution_funds.py`)

筛选机构持有占比高于指定阈值的基金：
- 可自定义机构持有占比阈值（默认 30%）
- 可设置目标数量
- 自动跳过货币基金

**使用方法：**
```python
# 修改阈值和目标数量
threshold = 30.0    # 机构持有占比高于 30%
target_count = 100  # 找到 100 只后停止
```

**输出：** `output/institution_funds_{timestamp}.csv`

### 3. 钉钉机器人消息通知 (`dingtalk_bot/`)

发送消息到钉钉群聊的机器人工具：
- 支持文本消息
- 支持 Markdown 消息
- 支持@所有人或指定用户
- 使用配置文件管理敏感凭证

**配置方法：**

1. 复制配置示例文件：
```bash
cp dingtalk_bot/config.json.example dingtalk_bot/config.json
```

2. 编辑 `dingtalk_bot/config.json`，填入你的机器人凭证：
```json
{
    "access_token": "你的 access_token",
    "secret": "你的加签密钥"
}
```

3. 运行测试：
```bash
python dingtalk_bot/dingtalk_bot.py
```

**注意：** `config.json` 已添加到 `.gitignore`，不会被提交到版本控制系统。

**输出：** 钉钉群聊消息

## 依赖

- Python 3.x
- requests
- pathlib (内置)
- json (内置)
- csv (内置)
- re (内置)

## 安装

```bash
pip install requests
```

## 运行

```bash
# 运行基金收益走势分析
python fetch_fund_data/fetch_fund_data.py

# 运行机构持有基金筛选
python institution_funds/find_institution_funds.py
```

## 数据源

所有数据来自 [天天基金网](http://fund.eastmoney.com/)

## 输出示例

### 机构持有基金筛选结果

| 基金代码 | 基金名称 | 机构持有占比 (%) | 个人持有占比 (%) | 基金规模 (亿元) |
|---------|---------|----------------|----------------|---------------|
| xxxxxx  | xxxx    | 85.23          | 14.77          | 12.34         |

### 基金收益走势

| 日期 | 单位净值 | 累计净值 | 日增长率 (%) | 累计收益率 (%) |
|-----|---------|---------|------------|--------------|
| 2025-03-01 | 1.234 | 1.567 | 0.52 | 5.67 |

## License

MIT License
