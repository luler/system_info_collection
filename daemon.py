# coding=utf-8
import os
import platform
import signal
import sys
import time

import psutil

# 确保能导入app模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import app.SystemInfoCollection as SystemInfoCollection

PID_FILE = os.path.abspath('./runtime/system_info_collection.pid')


def is_win():
    return platform.system() == 'Windows'


def get_process_from_pid_file():
    """通过PID文件安全地获取psutil.Process对象"""
    if not os.path.isfile(PID_FILE):
        return None

    with open(PID_FILE, 'r') as f:
        try:
            pid = int(f.read().strip())
        except (ValueError, TypeError):
            return None

    try:
        p = psutil.Process(pid)
        # --- 核心安全检查：检查进程命令行 ---
        # 确保它是由python启动，并且运行的是当前这个daemon.py文件
        cmdline = p.cmdline()
        if 'python' in os.path.basename(cmdline[0]) and os.path.abspath(cmdline[1]) == os.path.abspath(__file__):
            return p
    except psutil.NoSuchProcess:
        return None
    return None


def start():
    """启动守护进程"""
    if get_process_from_pid_file():
        print("Process is already running.")
        return

    if is_win():
        print("Daemon mode is not supported on Windows. Running in foreground.")
        # 在Windows上，直接在前台运行
        main_process()
    else:
        # --- 标准的守护进程化流程 ---
        pid = os.fork()
        if pid > 0:  # 父进程
            sys.exit(0)

        os.setsid()  # 创建新会话
        os.umask(0)  # 设置文件掩码

        # 第二次fork，确保进程不会重新获得控制终端
        pid = os.fork()
        if pid > 0:  # 第一个子进程
            sys.exit(0)

        # 写入新的PID
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))

        print("Starting daemon process...")
        main_process()


def stop():
    """优雅地停止守护进程"""
    print("Stopping daemon process...")
    p = get_process_from_pid_file()
    if not p:
        print("Process not found or PID file is invalid.")
        # 如果找不到进程但PID文件存在，最好清理一下
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
        return

    # 1. 尝试优雅终止 (SIGTERM)
    p.terminate()  # 发送SIGTERM
    try:
        # 等待最多5秒
        p.wait(timeout=5)
        print("Process stopped gracefully.")
    except psutil.TimeoutExpired:
        # 2. 如果超时，强制终止 (SIGKILL)
        print("Process did not terminate gracefully. Forcing kill...")
        p.kill()  # 发送SIGKILL
        print("Process killed.")

    # 清理PID文件
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)


def status():
    """检查守护进程状态"""
    p = get_process_from_pid_file()
    if p:
        print(f"Process is running with PID {p.pid}.")
    else:
        print("Process is stopped.")


def main_process():
    """程序的主业务逻辑入口"""
    collector = SystemInfoCollection.SystemInfoCollection()

    # 设置信号处理器，以便优雅地响应 'stop' 命令
    def signal_handler(signum, frame):
        collector.stop()

    signal.signal(signal.SIGTERM, signal_handler)

    try:
        collector.start()
    except KeyboardInterrupt:
        # 响应 Ctrl+C
        collector.stop()
    finally:
        collector.write_log("Collector process finished.")
        # 确保进程退出时删除PID文件
        if os.path.exists(PID_FILE) and not is_win():
            os.remove(PID_FILE)


if __name__ == '__main__':
    if is_win() and len(sys.argv) == 1:
        # 在Windows上无参数运行时，直接启动
        action = 'start'
    elif len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} [start|stop|restart|status]")
        sys.exit(1)
    else:
        action = sys.argv[1]

    if action == 'start':
        start()
    elif action == 'stop':
        stop()
    elif action == 'restart':
        stop()
        # 等待一小会确保端口等资源释放
        time.sleep(1)
        start()
    elif action == 'status':
        status()
    else:
        print(f"Unknown action: '{action}'. Use [start|stop|restart|status].")
