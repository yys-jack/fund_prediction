"""
Fund Prediction - 核心模块测试
"""

import unittest
from core.config import load_config, get_fund_code, get_output_dir
from core.http_client import get_session, fetch_text
from core.tiantian_api import get_fund_info, get_fund_list


class TestConfig(unittest.TestCase):
    """配置管理测试"""

    def test_load_config(self):
        """测试加载配置"""
        config = load_config()
        self.assertIn('fund_code', config)
        self.assertIn('fund_codes', config)

    def test_get_fund_code(self):
        """测试获取基金代码"""
        fund_code = get_fund_code()
        self.assertIsInstance(fund_code, str)
        self.assertEqual(len(fund_code), 6)

    def test_get_output_dir(self):
        """测试获取输出目录"""
        output_dir = get_output_dir()
        self.assertTrue(output_dir.exists())


class TestHTTPClient(unittest.TestCase):
    """HTTP 客户端测试"""

    def test_get_session(self):
        """测试创建 Session"""
        session = get_session()
        self.assertIsNotNone(session)
        self.assertIn('User-Agent', session.headers)

    def test_fetch_text(self):
        """测试获取文本"""
        content = fetch_text('https://www.example.com')
        self.assertIsInstance(content, str)


class TestTiantianAPI(unittest.TestCase):
    """天天基金 API 测试"""

    def test_get_fund_info(self):
        """测试获取基金信息"""
        fund_info = get_fund_info('161725')
        self.assertIn('code', fund_info)
        self.assertEqual(fund_info['code'], '161725')

    def test_get_fund_list(self):
        """测试获取基金列表"""
        fund_list = get_fund_list()
        self.assertIsInstance(fund_list, list)
        # 不检查具体长度，因为网络请求可能失败


if __name__ == '__main__':
    unittest.main()
