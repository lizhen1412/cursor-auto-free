#!/usr/bin/python3
# -*- coding: utf-8 -*-

from DrissionPage import ChromiumOptions, Chromium
from DrissionPage.common import Keys
import time
import re
import sys
import os


def get_extension_path():
    """
    获取插件的路径。

    该函数首先获取当前工作目录作为根目录，然后尝试通过连接“turnstilePatch”来构建插件路径。
    如果系统属性中包含'_MEIPASS'，表明程序正在打包环境中运行，此时插件路径将被设置为打包环境中的相应位置。
    函数会检查这个路径是否存在，如果不存在，则抛出一个文件找不到异常。
    如果路径存在，函数将返回该路径。

    Returns:
        str: 插件的路径。

    Raises:
        FileNotFoundError: 如果插件路径不存在。
    """
    # 获取当前工作目录作为根目录
    root_dir = os.getcwd()
    # 尝试构建插件路径
    extension_path = os.path.join(root_dir, "turnstilePatch")

    # 检查是否在打包环境中运行
    if hasattr(sys, "_MEIPASS"):
        print("运行在打包环境中")
        # 在打包环境中重新构建插件路径
        extension_path = os.path.join(sys._MEIPASS, "turnstilePatch")

    # 打印尝试加载的插件路径
    print(f"尝试加载插件路径: {extension_path}")

    # 检查插件路径是否存在
    if not os.path.exists(extension_path):
        # 如果不存在，抛出异常
        raise FileNotFoundError(
            f"插件不存在: {extension_path}\n请确保 turnstilePatch 文件夹在正确位置"
        )

    # 返回插件路径
    return extension_path



def get_browser_options():
    """
    获取浏览器配置选项。

    该函数创建并配置一个Chromium浏览器的选项对象。它尝试添加一个扩展，
    设置用户代理字符串，配置一些浏览器偏好设置，并根据操作系统进行特定设置。

    Returns:
        ChromiumOptions: 配置好的Chromium浏览器选项对象。
    """
    # 创建ChromiumOptions对象
    co = ChromiumOptions()

    # 尝试添加扩展，如果文件找不到则捕获异常并打印警告
    try:
        extension_path = get_extension_path()
        co.add_extension(extension_path)
    except FileNotFoundError as e:
        print(f"警告: {e}")

    # 设置用户代理字符串
    co.set_user_agent(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.6723.92 Safari/537.36"
    )

    # 禁用凭证服务
    co.set_pref("credentials_enable_service", False)

    # 隐藏崩溃恢复提示
    co.set_argument("--hide-crash-restore-bubble")

    # 自动选择可用的端口
    co.auto_port()

    # Mac 系统特殊处理
    if sys.platform == "darwin":
        # 在Mac系统中禁用沙箱模式
        co.set_argument("--no-sandbox")
        # 在Mac系统中禁用GPU加速
        co.set_argument("--disable-gpu")

    # 返回配置好的ChromiumOptions对象
    return co



def get_veri_code(username):
    """
    获取验证码

    通过自动化浏览器操作，访问临时邮箱网站，生成并提取验证码

    参数:
    username (str): 用户名，用于生成临时邮箱地址

    返回:
    str: 提取的验证码，如果未找到则为 None
    """
    # 使用相同的浏览器配置
    co = get_browser_options()
    # 创建浏览器实例
    browser = Chromium(co)
    code = None

    try:
        # 获取当前标签页
        tab = browser.latest_tab
        # 重置turnstile
        tab.run_js("try { turnstile.reset() } catch(e) { }")

        # 打开临时邮箱网站
        tab.get("https://tempmail.plus/zh")
        time.sleep(2)

        # 设置邮箱用户名
        while True:
            # 如果找到输入框，则点击并删除之前的内容
            if tab.ele("@id=pre_button"):
                # 点击输入框
                tab.actions.click("@id=pre_button")
                time.sleep(1)
                # 删除之前的内容
                tab.run_js('document.getElementById("pre_button").value = ""')

                # 输入新用户名并回车
                tab.actions.input(username).key_down(Keys.ENTER).key_up(Keys.ENTER)
                break
            time.sleep(1)

        # 等待并获取新邮件
        while True:
            # 检查是否有新邮件
            new_mail = tab.ele("@class=mail")
            # 如果有新邮件，则点击并获取邮件内容
            if new_mail:
                # 如果邮件内容不为空，则点击邮件
                if new_mail.text:
                    print("最新的邮件：", new_mail.text)
                    # 点击邮件
                    tab.actions.click("@class=mail")
                    break
                else:
                    print(new_mail)
                    break
            time.sleep(1)

        # 提取验证码
        if tab.ele("@class=overflow-auto mb-20"):
            # 提取邮件内容
            email_content = tab.ele("@class=overflow-auto mb-20").text
            # 匹配验证码
            verification_code = re.search(
                r"verification code is (\d{6})", email_content
            )

            # 如果找到验证码，则提取并打印
            if verification_code:
                code = verification_code.group(1)
                print("验证码：", code)
            else:
                print("未找到验证码")

        # 删除邮件
        if tab.ele("@id=delete_mail"):
            tab.actions.click("@id=delete_mail")
            time.sleep(1)

        # 确认删除
        if tab.ele("@id=confirm_mail"):
            tab.actions.click("@id=confirm_mail")
            print("删除邮件")

    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        browser.quit()

    return code



# 测试运行
if __name__ == "__main__":
    test_username = "test_user"  # 替换为你要测试的用户名
    code = get_veri_code(test_username)
    print(f"获取到的验证码: {code}")
