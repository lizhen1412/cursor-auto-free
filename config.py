#!/usr/bin/python3
# -*- coding: utf-8 -*-

from dotenv import load_dotenv
import os
import sys
from logger import logging


class Config:
    def __init__(self):
        # 获取应用程序的根目录路径
        if getattr(sys, "frozen", False):
            # 如果是打包后的可执行文件
            application_path = os.path.dirname(sys.executable)
        else:
            # 如果是开发环境
            application_path = os.path.dirname(os.path.abspath(__file__))

        # 指定 .env 文件的路径
        dotenv_path = os.path.join(application_path, ".env")

        if not os.path.exists(dotenv_path):
            raise FileNotFoundError(f"文件 {dotenv_path} 不存在")

        # 加载 .env 文件
        load_dotenv(dotenv_path)

        self.imap = False
        self.temp_mail = os.getenv("TEMP_MAIL", "").strip().split("@")[0]
        self.temp_mail_epin = os.getenv("TEMP_MAIL_EPIN", "").strip()
        self.temp_mail_ext = os.getenv("TEMP_MAIL_EXT", "").strip()
        self.domain = os.getenv("DOMAIN", "").strip()

        # 如果临时邮箱为null则加载IMAP
        if self.temp_mail == "null":
            self.imap = True
            self.imap_server = os.getenv("IMAP_SERVER", "").strip()
            self.imap_port = os.getenv("IMAP_PORT", "").strip()
            self.imap_user = os.getenv("IMAP_USER", "").strip()
            self.imap_pass = os.getenv("IMAP_PASS", "").strip()
            self.imap_dir = os.getenv("IMAP_DIR", "inbox").strip()

        self.check_config()

    def get_temp_mail(self):
        """
        获取临时邮箱地址

        此方法用于返回当前实例所持有的临时邮箱地址它没有参数，
        也不需要从外部获取任何信息直接返回实例变量 self.temp_mail

        Returns:
            str: 当前实例持有的临时邮箱地址
        """
        return self.temp_mail

    def get_temp_mail_epin(self):
        """
        获取临时邮箱的验证码

        该方法用于从实例的属性中获取临时邮箱的验证码这个验证码是临时邮箱服务提供商在验证邮箱时使用的代码或密钥

        Returns:
            str: 临时邮箱的验证码如果未定义或不可用，则可能返回空字符串或None
        """
        return self.temp_mail_epin

    def get_temp_mail_ext(self):
        """
        获取临时邮件的扩展名。
        Returns:
            str: 临时邮件的扩展名。
        """
        return self.temp_mail_ext

    def get_imap(self):
        """
        获取IMAP配置信息

        当self.imap为False时，表示没有IMAP配置信息，返回False
        否则，返回包含IMAP配置信息的字典，包括服务器地址、端口、用户名、密码及目录

        Returns:
            bool: 如果没有IMAP配置信息，则返回False
            dict: 如果有IMAP配置信息，则返回包含配置信息的字典
        """
        if not self.imap:
            return False
        return {
            "imap_server": self.imap_server,
            "imap_port": self.imap_port,
            "imap_user": self.imap_user,
            "imap_pass": self.imap_pass,
            "imap_dir": self.imap_dir,
        }

    def get_domain(self):
        """
        获取当前实例的域名信息。

        该方法无需额外参数，直接返回实例的 `domain` 属性，即域名。
        用于在需要的地方获取实例的域名信息，避免直接访问属性。

        :return: 当前实例的域名。
        """
        return self.domain

    def get_protocol(self):
        """获取邮件协议类型
        
        Returns:
            str: 'IMAP' 或 'POP3'
        """
        return os.getenv('IMAP_PROTOCOL', 'POP3')

    def check_config(self):
        """检查配置项是否有效

        检查规则：
        1. 如果使用 tempmail.plus，需要配置 TEMP_MAIL 和 DOMAIN
        2. 如果使用 IMAP，需要配置 IMAP_SERVER、IMAP_PORT、IMAP_USER、IMAP_PASS
        3. IMAP_DIR 是可选的
        """
        # 基础配置检查
        required_configs = {
            "domain": "域名",
        }

        # 检查基础配置
        for key, name in required_configs.items():
            if not self.check_is_valid(getattr(self, key)):
                raise ValueError(f"{name}未配置，请在 .env 文件中设置 {key.upper()}")

        # 检查邮箱配置
        if self.temp_mail != "null":
            # tempmail.plus 模式
            if not self.check_is_valid(self.temp_mail):
                raise ValueError("临时邮箱未配置，请在 .env 文件中设置 TEMP_MAIL")
        else:
            # IMAP 模式
            imap_configs = {
                "imap_server": "IMAP服务器",
                "imap_port": "IMAP端口",
                "imap_user": "IMAP用户名",
                "imap_pass": "IMAP密码",
            }

            for key, name in imap_configs.items():
                value = getattr(self, key)
                if value == "null" or not self.check_is_valid(value):
                    raise ValueError(
                        f"{name}未配置，请在 .env 文件中设置 {key.upper()}"
                    )

            # IMAP_DIR 是可选的，如果设置了就检查其有效性
            if self.imap_dir != "null" and not self.check_is_valid(self.imap_dir):
                raise ValueError(
                    "IMAP收件箱目录配置无效，请在 .env 文件中正确设置 IMAP_DIR"
                )

    def check_is_valid(self, value):
        """检查配置项是否有效

        Args:
            value: 配置项的值

        Returns:
            bool: 配置项是否有效
        """
        return isinstance(value, str) and len(str(value).strip()) > 0

    def print_config(self):
        if self.imap:
            logging.info(f"\033[32mIMAP服务器: {self.imap_server}\033[0m")
            logging.info(f"\033[32mIMAP端口: {self.imap_port}\033[0m")
            logging.info(f"\033[32mIMAP用户名: {self.imap_user}\033[0m")
            logging.info(f"\033[32mIMAP密码: {'*' * len(self.imap_pass)}\033[0m")
            logging.info(f"\033[32mIMAP收件箱目录: {self.imap_dir}\033[0m")
        if self.temp_mail != "null":
            logging.info(
                f"\033[32m临时邮箱: {self.temp_mail}{self.temp_mail_ext}\033[0m"
            )
        logging.info(f"\033[32m域名: {self.domain}\033[0m")


# 使用示例
if __name__ == "__main__":
    try:
        config = Config()
        print("环境变量加载成功！")
        config.print_config()
    except ValueError as e:
        print(f"错误: {e}")
