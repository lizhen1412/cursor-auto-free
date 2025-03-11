#!/usr/bin/python3
# -*- coding: utf-8 -*-

import warnings
import os
import platform
import subprocess
import time
import threading

# Ignore specific SyntaxWarning
warnings.filterwarnings("ignore", category=SyntaxWarning, module="DrissionPage")

CURSOR_LOGO = """
   ██████╗██╗   ██╗██████╗ ███████╗ ██████╗ ██████╗ 
  ██╔════╝██║   ██║██╔══██╗██╔════╝██╔═══██╗██╔══██╗
  ██║     ██║   ██║██████╔╝███████╗██║   ██║██████╔╝
  ██║     ██║   ██║██╔══██╗╚════██║██║   ██║██╔══██╗
  ╚██████╗╚██████╔╝██║  ██║███████║╚██████╔╝██║  ██║
   ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝
"""


class LoadingAnimation:
    # 初始化函数，用于设置对象的初始状态。
    # 参数: 无
    # 返回值: 无
    def __init__(self):
        # 定义一个布尔值变量，用于跟踪动画是否正在运行。
        self.is_running = False

        # 定义一个线程变量，用于存储动画运行时的线程对象。
        self.animation_thread = None


    # 开始动画线程并设置运行状态为True。
    # 参数:
    #   message (str): 动画显示的消息，默认值为"Building"。
    # 返回值:
    #   无返回值。
    def start(self, message="Building"):
        # 设置运行状态为True，表示动画开始。
        self.is_running = True

        # 创建并启动一个新线程，用于运行动画函数`_animate`，并将消息作为参数传递。
        self.animation_thread = threading.Thread(target=self._animate, args=(message,))
        # 开始线程
        self.animation_thread.start()


    # 停止动画的函数
    # 参数:
    #   self: 类实例对象，包含动画运行状态和线程信息
    # 返回值:
    #   无返回值
    def stop(self):
        # 设置动画运行状态为 False，标记动画停止
        self.is_running = False

        # 如果动画线程存在，等待线程结束
        if self.animation_thread:
            self.animation_thread.join()

        # 清除当前行的输出内容，确保终端界面整洁
        print("\r" + " " * 70 + "\r", end="", flush=True)


    # 动画效果函数，用于在控制台显示动态加载指示器。
    # 参数:
    #   message (str): 显示在动画前的提示信息。
    # 返回值:
    #   无返回值。
    def _animate(self, message):
        # 定义动画字符序列，用于循环显示动态效果。
        animation = "|/-\\"
        idx = 0
        # 当 self.is_running 为 True 时，持续显示动画。
        while self.is_running:
            # 打印当前的提示信息和动画字符，\r 用于回到行首覆盖前一帧内容。
            print(f"\r{message} {animation[idx % len(animation)]}", end="", flush=True)
            idx += 1
            # 每次循环暂停 0.1 秒，以控制动画速度。
            time.sleep(0.1)



def print_logo():
    """
    打印程序的Logo和提示信息。

    该函数没有参数。
    返回值：无。

    功能描述：
    - 使用ANSI转义序列设置文本颜色，打印一个预定义的Logo（CURSOR_LOGO）。
    - 打印一条居中的提示信息，内容为"Building Cursor Keep Alive..."。
    """
    # 打印带有青色（Cyan）颜色的Logo
    print("\033[96m" + CURSOR_LOGO + "\033[0m")

    # 打印黄色（Yellow）颜色的居中提示信息
    print("\033[93m" + "Building Cursor Keep Alive...".center(56) + "\033[0m\n")



def progress_bar(progress, total, prefix="", length=50):
    """
    打印一个动态进度条到控制台，用于显示任务的完成进度。

    参数:
        progress (int): 当前已完成的任务量。
        total (int): 任务总量。
        prefix (str): 进度条前缀字符串，默认为空字符串。
        length (int): 进度条的长度（字符数），默认为50。

    返回值:
        无返回值。该函数直接打印进度条到控制台。
    """
    # 计算进度条中需要填充的字符数量
    filled = int(length * progress // total)

    # 构造进度条字符串，使用"█"表示已完成部分，"░"表示未完成部分
    bar = "█" * filled + "░" * (length - filled)

    # 计算当前完成百分比并格式化为保留一位小数的字符串
    percent = f"{100 * progress / total:.1f}"

    # 打印进度条和完成百分比，使用\r实现动态刷新效果
    print(f"\r{prefix} |{bar}| {percent}% Complete", end="", flush=True)

    # 如果任务完成，打印换行符以结束进度条
    if progress == total:
        print()



def simulate_progress(message, duration=1.0, steps=20):
    """
    模拟一个带有进度条的任务执行过程。

    参数:
        message (str): 要显示的消息，通常用于描述当前任务。
        duration (float): 整个任务模拟的总持续时间（以秒为单位），默认值为 1.0 秒。
        steps (int): 将任务分为多少个步骤，默认值为 20。

    返回值:
        无返回值。
    """
    # 打印任务描述消息，使用蓝色字体以突出显示
    print(f"\033[94m{message}\033[0m")

    # 循环遍历每个步骤，逐步更新进度条
    for i in range(steps + 1):
        # 根据总时长和步骤数计算每一步的等待时间
        time.sleep(duration / steps)

        # 调用 progress_bar 函数显示当前进度
        progress_bar(i, steps, prefix="Progress:", length=40)



def filter_output(output):
    """
        过滤输出信息，仅保留包含特定关键字的行

        参数：
            output (str): 需要过滤的原始输出文本（通常包含多行信息）

        返回：
            str: 过滤后的文本，仅保留包含关键字的行（用换行符连接）
        """
    """ImportantMessage"""
    if not output:
        return ""
    important_lines = [] # 初始化保存重要信息的列表

    # 逐行处理原始输出
    for line in output.split("\n"):
        # Only keep lines containing specific keywords
        # 检查当前行是否包含任意一个指定关键字（不区分大小写）
        # 保留的关键字包括：error（错误）、failed（失败）、completed（完成）、directory（目录）
        if any(
            keyword in line.lower()
            for keyword in ["error:", "failed:", "completed", "directory:"]
        ):
            important_lines.append(line) # 满足条件的行加入重要信息列表
    # 将过滤后的重要行用换行符连接，还原为字符串格式返回
    return "\n".join(important_lines)


def build():
    """
    构建 CursorKeepAlive 应用程序以适用于当前操作系统。

    该函数清除屏幕，打印应用程序标志，并使用 PyInstaller 构建应用程序。
    它处理不同的操作系统（目前支持 Windows 和 macOS），并包括构建过程中的错误处理。
    构建成功后，它会将必要的配置文件复制到输出目录。
    """
    # Clear screen
    os.system("cls" if platform.system().lower() == "windows" else "clear")

    # Print logo
    print_logo()

    # 确定当前操作系统
    system = platform.system().lower()
    # 定义规范文件路径
    spec_file = os.path.join("CursorKeepAlive.spec")

    # if system not in ["darwin", "windows"]:
    #     print(f"\033[91mUnsupported operating system: {system}\033[0m")
    #     return

    # 根据操作系统定义输出目录
    output_dir = f"dist/{system if system != 'darwin' else 'mac'}"

    # Create output directory
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    # 运行模拟进度条
    simulate_progress("Creating output directory...", 0.5)

    # Run PyInstaller with loading animation
    # 准备 PyInstaller 命令
    pyinstaller_command = [
        "pyinstaller",
        spec_file,
        "--distpath",
        output_dir,
        "--workpath",
        f"build/{system}",
        "--noconfirm",
    ]

    # 初始化加载动画
    loading = LoadingAnimation()
    try:
        # 运行 PyInstaller 并捕获输出
        simulate_progress("Running PyInstaller...", 2.0)
        # 输出正在构建运行中
        loading.start("Building in progress")


        result = subprocess.run(
            pyinstaller_command, check=True, capture_output=True, text=True
        )
        loading.stop()

        if result.stderr:
            filtered_errors = [
                line
                for line in result.stderr.split("\n")
                if any(
                    keyword in line.lower()
                    for keyword in ["error:", "failed:", "completed", "directory:"]
                )
            ]
            if filtered_errors:
                print("\033[93mBuild Warnings/Errors:\033[0m")
                print("\n".join(filtered_errors))

    except subprocess.CalledProcessError as e:
        loading.stop()
        print(f"\033[91mBuild failed with error code {e.returncode}\033[0m")
        if e.stderr:
            print("\033[91mError Details:\033[0m")
            print(e.stderr)
        return
    except FileNotFoundError:
        loading.stop()
        print(
            "\033[91mError: Please ensure PyInstaller is installed (pip install pyinstaller)\033[0m"
        )
        return
    except KeyboardInterrupt:
        loading.stop()
        print("\n\033[91mBuild cancelled by user\033[0m")
        return
    finally:
        loading.stop()

    # Copy config file
    if os.path.exists("config.ini.example"):
        simulate_progress("Copying configuration file...", 0.5)
        if system == "windows":
            subprocess.run(
                ["copy", "config.ini.example", f"{output_dir}\\config.ini"], shell=True
            )
        else:
            subprocess.run(["cp", "config.ini.example", f"{output_dir}/config.ini"])

    # Copy .env.example file
    # 复制 .env.example 文件 到 输出目录
    if os.path.exists(".env.example"):
        # 运行模拟进度条
        simulate_progress("Copying environment file...", 0.5)
        # 如果系统是 Windows，则使用 copy 命令，否则使用 cp 命令
        if system == "windows":
            subprocess.run(["copy", ".env.example", f"{output_dir}\\.env"], shell=True)
        else:
            subprocess.run(["cp", ".env.example", f"{output_dir}/.env"])

    print(
        f"\n\033[92mBuild completed successfully! Output directory: {output_dir}\033[0m"
    )


if __name__ == "__main__":
    build()
