"""
钉钉机器人消息发送工具
文档：https://open.dingtalk.com/document/robots/customize-robot-security-settings
"""

import hmac
import hashlib
import base64
import urllib.parse
import requests
import time
import json
from pathlib import Path


def load_config() -> dict:
    """
    从 config.json 加载配置

    Returns:
        包含 access_token 和 secret 的字典

    Raises:
        FileNotFoundError: 当 config.json 不存在时
        json.JSONDecodeError: 当 config.json 格式不正确时
    """
    config_path = Path(__file__).parent / "config.json"

    if not config_path.exists():
        raise FileNotFoundError(
            f"配置文件不存在：{config_path}\n"
            f"请参考 config.json.example 创建配置文件"
        )

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    if "access_token" not in config:
        raise ValueError("配置文件缺少 access_token")
    if "secret" not in config:
        raise ValueError("配置文件缺少 secret")

    return config


class DingTalkBot:
    """钉钉机器人消息发送类"""

    def __init__(self, access_token: str, secret: str = None):
        """
        初始化钉钉机器人

        Args:
            access_token: 机器人 access_token
            secret: 加签密钥（如果设置了签名安全设置）
        """
        self.access_token = access_token
        self.secret = secret
        self.webhook = f"https://oapi.dingtalk.com/robot/send?access_token={access_token}"

    def generate_sign(self) -> str:
        """
        生成签名

        使用 HmacSHA256 算法，将 timestamp 和 secret 进行签名

        Returns:
            签名后的字符串（URL 编码）
        """
        if not self.secret:
            return ""

        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')

        hmac_code = hmac.new(
            secret_enc,
            string_to_sign_enc,
            digestmod=hashlib.sha256
        ).digest()

        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        return f"&timestamp={timestamp}&sign={sign}"

    def send_text(self, content: str, mentioned_all: bool = False, mentioned_users: list = None) -> dict:
        """
        发送文本消息

        Args:
            content: 消息内容
            mentioned_all: 是否@所有人
            mentioned_users: 被@人的用户 ID 列表

        Returns:
            API 响应结果
        """
        webhook = self.webhook
        if self.secret:
            webhook += self.generate_sign()

        headers = {'Content-Type': 'application/json; charset=utf-8'}

        data = {
            "msgtype": "text",
            "text": {
                "content": content
            },
            "at": {
                "isAtAll": mentioned_all,
                "atUserIds": mentioned_users or []
            }
        }

        response = requests.post(webhook, json=data, headers=headers, timeout=10)
        return response.json()

    def send_markdown(self, title: str, text: str, mentioned_all: bool = False) -> dict:
        """
        发送 Markdown 消息

        Args:
            title: 消息标题
            text: Markdown 格式的消息内容
            mentioned_all: 是否@所有人

        Returns:
            API 响应结果
        """
        webhook = self.webhook
        if self.secret:
            webhook += self.generate_sign()

        headers = {'Content-Type': 'application/json; charset=utf-8'}

        data = {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": text
            },
            "at": {
                "isAtAll": mentioned_all
            }
        }

        response = requests.post(webhook, json=data, headers=headers, timeout=10)
        return response.json()


def main():
    """测试发送消息"""
    import sys
    import io
    # 解决 Windows 中文乱码问题
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    # 从配置文件加载配置信息
    try:
        config = load_config()
        ACCESS_TOKEN = config["access_token"]
        SECRET = config["secret"]
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
        print(f"配置加载失败：{e}")
        return

    # 创建机器人实例
    bot = DingTalkBot(access_token=ACCESS_TOKEN, secret=SECRET)

    # 发送测试消息
    print("正在发送测试消息...")
    result = bot.send_text("你好")

    print(f"发送结果：{result}")

    if result.get('errcode') == 0:
        print("消息发送成功！")
    else:
        print(f"消息发送失败：{result}")


if __name__ == "__main__":
    main()
