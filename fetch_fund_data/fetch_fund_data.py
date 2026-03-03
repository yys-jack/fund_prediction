"""
获取基金近 1 年收益走势并保存为 CSV
基金代码：161725（招商中证白酒指数）

数据源：天天基金网网页 JS 数据 + 历史交易数据 API
"""

import requests
import csv
import json
import re
from datetime import datetime
from pathlib import Path

# 设置输出目录为 output
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_fund_history_from_js(fund_code: str) -> list:
    """
    从天天基金网的 JS 文件获取历史净值数据和累计净值数据
    """
    url = f"https://fund.eastmoney.com/pingzhongdata/{fund_code}.js"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"http://fund.eastmoney.com/{fund_code}.html",
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        content = response.text

        # 提取单位净值数据
        net_worth_match = re.search(r'Data_netWorthTrend\s*=\s*(\[.*?\]);', content, re.DOTALL)

        # 提取累计净值数据 (数组格式 [[timestamp, value], ...])
        ac_worth_match = re.search(r'Data_ACWorthTrend\s*=\s*(\[.*?\]);', content, re.DOTALL)

        result = []

        if net_worth_match:
            net_worth_data = json.loads(net_worth_match.group(1))
            print(f"获取到 {len(net_worth_data)} 条净值数据")

            # 解析累计净值数据 (数组格式 [[timestamp, value], ...])
            ac_worth_dict = {}
            if ac_worth_match:
                try:
                    ac_worth_raw = json.loads(ac_worth_match.group(1))
                    if ac_worth_raw and isinstance(ac_worth_raw[0], list):
                        for item in ac_worth_raw:
                            if len(item) >= 2:
                                ac_worth_dict[str(item[0])] = item[1]
                    print(f"获取到 {len(ac_worth_dict)} 条累计净值数据")
                except Exception as e:
                    print(f"解析累计净值失败：{e}")

            # 合并数据
            for item in net_worth_data:
                x_val = str(item.get('x', ''))
                y_val = item.get('y', 0)

                # 获取对应的累计净值
                ac_value = ac_worth_dict.get(x_val, y_val)

                result.append({
                    'x': x_val,
                    'DWJZ': y_val,
                    'LJJZ': ac_value,
                })

            if result:
                print(f"数据示例：{result[0]}")
                print(f"累计净值示例：LJJZ={result[0]['LJJZ']}")

        return result

    except requests.exceptions.RequestException as e:
        print(f"请求错误：{e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}")
        return []
    except Exception as e:
        print(f"解析数据失败：{e}")
        return []


def get_fund_history_detail(fund_code: str) -> list:
    """
    获取基金历史交易数据（包含日增长率）
    使用天天基金网 API
    """
    url = "http://api.fund.eastmoney.com/f10/lsjz"

    params = {
        "fundCode": fund_code,
        "pageIndex": 1,
        "pageSize": 365,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": f"http://fund.eastmoney.com/{fund_code}.html",
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'

        data = response.json()

        if data.get("ErrCode") == 0 and data.get("Data"):
            lsjz_list = data["Data"]["LSJZList"]
            print(f"获取到 {len(lsjz_list)} 条历史交易数据")
            return lsjz_list
        else:
            print(f"获取历史交易数据失败：{data.get('ErrMsg', '未知错误')}")
            return []

    except requests.exceptions.RequestException as e:
        print(f"请求错误：{e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON 解析失败：{e}")
        return []
    except Exception as e:
        print(f"解析数据失败：{e}")
        return []


def timestamp_to_date(timestamp_ms: str) -> str:
    """
    将毫秒时间戳转换为日期字符串
    """
    try:
        timestamp = int(float(timestamp_ms))
        dt = datetime.fromtimestamp(timestamp / 1000)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return str(timestamp_ms)


def filter_last_year(data: list) -> list:
    """
    筛选近 1 年的数据
    """
    if not data:
        return []

    now = datetime.now()
    one_year_ago = now.replace(year=now.year - 1)

    result = []
    for item in data:
        try:
            x_val = item.get("x", "")
            date_str = timestamp_to_date(x_val)

            item_date = datetime.strptime(date_str, "%Y-%m-%d")

            if item_date >= one_year_ago:
                item["_date_str"] = date_str
                result.append(item)
        except Exception:
            continue

    return result


def merge_and_process_data(js_data: list, detail_data: list) -> list:
    """
    合并 JS 数据和详细交易数据，计算日增长率
    """
    # 创建详细数据映射（用于获取日增长率）
    detail_map = {}
    for item in detail_data:
        date = item.get("FSRQ", "")
        detail_map[date] = {
            "DWJZ": float(item.get("DWJZ", 0)),
            "LJJZ": float(item.get("LJJZ", 0)),
            "JZZZL": float(str(item.get("JZZZL", "0")).replace("%", "")),
        }

    result = []
    for item in js_data:
        date_str = item.get("_date_str", "")
        net_value = float(item.get("DWJZ", 0))

        # 从详细数据中获取信息
        detail = detail_map.get(date_str, {})

        if detail:
            accumulated_value = detail.get("LJJZ", net_value)
            daily_growth = detail.get("JZZZL", 0.0)
        else:
            # 如果没有详细数据，使用累计净值
            accumulated_value = float(item.get("LJJZ", net_value))
            # 通过前后两天的净值计算增长率
            daily_growth = 0.0

        result.append({
            "日期": date_str,
            "单位净值": net_value,
            "累计净值": accumulated_value,
            "日增长率 (%)": daily_growth,
        })

    # 按日期排序
    result.sort(key=lambda x: x["日期"])

    # 如果日增长率都是 0，手动计算
    if all(item["日增长率 (%)"] == 0.0 for item in result):
        print("详细数据中没有增长率，将通过净值计算...")
        for i in range(1, len(result)):
            prev_value = result[i - 1]["单位净值"]
            curr_value = result[i]["单位净值"]
            if prev_value > 0:
                growth = (curr_value - prev_value) / prev_value * 100
                result[i]["日增长率 (%)"] = round(growth, 2)

    # 计算累计收益率
    if result:
        base_value = result[0]["单位净值"]
        for item in result:
            if base_value > 0:
                item["累计收益率 (%)"] = round(
                    (item["单位净值"] - base_value) / base_value * 100, 2
                )
            else:
                item["累计收益率 (%)"] = 0.0

    return result


def save_to_csv(data: list, fund_code: str, filename: str = None):
    """
    保存数据到 CSV 文件
    """
    if not data:
        print("没有数据可保存")
        return None

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"fund_{fund_code}_{timestamp}.csv"

    # 保存到 output 目录
    output_path = OUTPUT_DIR / filename
    fieldnames = ["日期", "单位净值", "累计净值", "日增长率 (%)", "累计收益率 (%)"]

    try:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)

        print(f"\n数据已保存到：{output_path}")
        print(f"共保存 {len(data)} 条记录")
        return output_path
    except Exception as e:
        print(f"保存文件失败：{e}")
        return None


def main():
    fund_code = "161725"

    print(f"正在获取基金 {fund_code} 的数据...")
    print(f"获取近 1 年的收益走势数据")
    print()

    # 1. 从 JS 文件获取净值和累计净值数据
    print("1. 获取净值和累计净值数据...")
    js_data = get_fund_history_from_js(fund_code)

    if not js_data:
        print("未能获取到基金数据")
        return

    # 2. 从 API 获取历史交易数据（用于获取日增长率）
    print("\n2. 获取历史交易数据（含日增长率）...")
    detail_data = get_fund_history_detail(fund_code)

    # 3. 筛选近 1 年的数据
    print("\n3. 筛选近 1 年数据...")
    filtered_data = filter_last_year(js_data)
    print(f"筛选后剩余 {len(filtered_data)} 条数据")

    # 4. 合并和处理数据
    print("\n4. 合并和处理数据...")
    result_data = merge_and_process_data(filtered_data, detail_data)

    # 5. 保存到 CSV
    print("\n5. 保存数据到 CSV...")
    output_file = f"fund_{fund_code}_1year.csv"
    save_to_csv(result_data, fund_code, output_file)

    # 打印摘要信息
    if result_data:
        print("\n" + "=" * 50)
        print("=== 收益走势摘要 ===")
        print("=" * 50)
        print(f"最早日期：{result_data[0]['日期']}")
        print(f"最新日期：{result_data[-1]['日期']}")
        print(f"起始单位净值：{result_data[0]['单位净值']}")
        print(f"起始累计净值：{result_data[0]['累计净值']}")
        print(f"最新单位净值：{result_data[-1]['单位净值']}")
        print(f"最新累计净值：{result_data[-1]['累计净值']}")
        print(f"累计收益率：{result_data[-1]['累计收益率 (%)']}%")
        print("=" * 50)

        # 打印前几天数据检查
        print("\n前 5 条数据详情:")
        for item in result_data[:5]:
            print(f"  {item['日期']}: 单位净值={item['单位净值']}, 累计净值={item['累计净值']}, 日增长率={item['日增长率 (%)']}%")


if __name__ == "__main__":
    main()
