#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from DrissionPage import ChromiumOptions, Chromium
import sys
import os
import logging
from dotenv import load_dotenv

load_dotenv()


class BrowserManager:
    # 初始化类的实例
    # 参数: 无
    # 返回值: 无
    # 功能: 定义一个实例变量 `browser`，并将其初始化为 None。
    #       该变量可能用于后续存储与浏览器相关的对象或状态。
    def __init__(self):
        self.browser = None

    def init_browser(self, user_agent=None):
        """
        初始化浏览器实例。

        参数:
            user_agent (str, optional): 指定的用户代理字符串，用于设置浏览器的User-Agent头。
                                         如果未提供，则使用默认值或配置中的值。默认为None。

        返回:
            browser: 初始化后的浏览器实例，类型为Chromium。

        说明:
            该方法通过调用内部方法_get_browser_options生成浏览器选项，
            并使用这些选项创建一个Chromium浏览器实例。
        """
        # 获取浏览器选项，可能包含用户代理等配置
        co = self._get_browser_options(user_agent)

        # 使用生成的选项初始化Chromium浏览器实例
        self.browser = Chromium(co)

        return self.browser


    def _get_browser_options(self, user_agent=None):
        """
        获取浏览器配置。

        参数:
            user_agent (str, optional): 指定的用户代理字符串。如果提供，则设置为浏览器的用户代理。默认为 None。

        返回:
            ChromiumOptions: 配置完成的 ChromiumOptions 对象，包含浏览器的各种选项和设置。
        """
        co = ChromiumOptions()

        # 尝试加载扩展插件，若插件路径不存在则记录警告日志
        try:
            extension_path = self._get_extension_path("turnstilePatch")
            co.add_extension(extension_path)
        except FileNotFoundError as e:
            logging.warning(f"警告: {e}")

        # 如果环境变量中设置了浏览器路径，则使用该路径
        browser_path = os.getenv("BROWSER_PATH")
        if browser_path:
            # 设置浏览器路径
            co.set_paths(browser_path=browser_path)

        # 禁用凭据服务并隐藏崩溃恢复提示
        co.set_pref("credentials_enable_service", False)
        # 隐藏崩溃恢复提示
        co.set_argument("--hide-crash-restore-bubble")

        # 如果环境变量中设置了代理，则配置代理
        proxy = os.getenv("BROWSER_PROXY")
        if proxy:
            co.set_proxy(proxy)

        # 自动分配端口
        co.auto_port()

        # 如果提供了用户代理，则设置用户代理
        if user_agent:
            co.set_user_agent(user_agent)

        # 根据环境变量决定是否启用无头模式
        co.headless(
            os.getenv("BROWSER_HEADLESS", "True").lower() == "true"
        )

        # 针对 Mac 系统的特殊处理，禁用沙盒和 GPU 加速
        if sys.platform == "darwin":
            co.set_argument("--no-sandbox")
            co.set_argument("--disable-gpu")

        return co


    def _get_extension_path(self, exname='turnstilePatch'):
        """
        获取插件路径。

        参数:
            exname (str): 插件名称，默认值为 'turnstilePatch'。

        返回值:
            str: 插件的完整路径。

        异常:
            FileNotFoundError: 如果插件路径不存在，则抛出此异常。
        """
        # 获取当前工作目录作为根目录
        root_dir = os.getcwd()
        extension_path = os.path.join(root_dir, exname)

        # 如果程序是通过 PyInstaller 打包运行的，使用 sys._MEIPASS 作为根目录
        if hasattr(sys, "_MEIPASS"):
            extension_path = os.path.join(sys._MEIPASS, exname)

        # 检查插件路径是否存在，如果不存在则抛出异常
        if not os.path.exists(extension_path):
            raise FileNotFoundError(f"插件不存在: {extension_path}")

        return extension_path


    def quit(self):
        """
        关闭浏览器实例。

        参数:
            无

        返回值:
            无

        功能描述:
            该方法用于安全地关闭当前的浏览器实例。如果浏览器实例存在，
            则尝试调用其 quit() 方法以释放资源。如果在关闭过程中发生异常，
            则捕获并忽略该异常，确保程序不会因此中断。
        """
        if self.browser:
            try:
                # 尝试调用浏览器实例的 quit() 方法以关闭浏览器
                self.browser.quit()
            except:
                # 捕获并忽略关闭浏览器时可能发生的异常
                pass

