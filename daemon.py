# coding=utf-8
import os
import platform
import signal
import sys

import psutil

import app.SystemInfoCollection as SystemInfoCollection


def get_pid_file():
    return os.path.abspath('./runtime/system_info_collection.pid')


def is_win():
    mark = platform.system()
    res = False
    if mark == 'Windows':
        res = True
    return res


def start():
    if not is_win():  # 一般不是win，可进入守护进程
        pid_file = get_pid_file()
        pid = os.fork()
        if pid:  ##父进程
            sys.exit(0)
        # 进入子进程，以下设置while True执行，将成守护进程
        # os.chdir('/')  # 子进程会继承父进程的工作目录，如果在子进程运行过程中，需要删除父进程的工作目录则会产生漏洞问题，进程去到根目录，则可避免这种问题
        # 子进程默认继承父进程的umask（文件权限掩码），重设为0（完全控制），以免影响程序读写文件
        os.umask(0)  # 当前程序可注释掉
        # 创建新会话，成为进程组组长
        os.setsid()

        f = open(pid_file, 'w+')
        f.write(str(os.getpid()))
        f.close()

    SystemInfoCollection.SystemInfoCollection().start()
    print('Starting the process successfully')


def kill():
    # 记录守护进程pid
    pid_file = get_pid_file()
    # kill历史进程，存在问题可能kill调其他进程，这里不做这种打算
    if os.path.isfile(pid_file):
        f = open(pid_file, 'r')
        id = f.read()
        f.close()
        id = int(id)
        try:
            has = 'python' in psutil.Process(id).name()
        except:
            has = False
        if has:
            os.kill(id, signal.SIGKILL)
        os.remove(pid_file)


def status():
    # 记录守护进程pid
    pid_file = get_pid_file()
    # kill历史进程，存在问题可能kill调其他进程，这里不做这种打算
    if os.path.isfile(pid_file):
        f = open(pid_file, 'r')
        id = f.read()
        f.close()
        id = int(id)
        try:
            has = 'python' in psutil.Process(id).name()
        except:
            has = False
        if has:
            print('process is running at ' + str(id))
            exit()
    print('process is stop')


if __name__ == '__main__':
    action = sys.argv[1] if len(sys.argv) >= 2 else 'start'
    action = action if action in ['start', 'stop', 'status', 'restart'] else 'start'

    if action in ['start', 'restart']:
        if not is_win():
            kill()
        start()
    elif action == 'stop':
        if is_win():
            print('暂不支持window下关闭进程')
            exit()
        kill()
        print('process has been stoped')
    else:
        if is_win():
            print('暂不支持window下查看进程状态')
            exit()
        status()
