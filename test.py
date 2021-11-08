# coding=utf-8
import os
import sys
import time
import atexit
import multiprocessing

pid = os.fork()

if pid:  ##父进程
    sys.exit(0)
# 进入子进程，以下设置while True执行，将成守护进程
os.chdir('/')  # 子进程会继承父进程的工作目录，如果在子进程运行过程中，需要删除父进程的工作目录则会产生漏洞问题，进程去到根目录，则可避免这种问题
# 子进程默认继承父进程的umask（文件权限掩码），重设为0（完全控制），以免影响程序读写文件
os.umask(0)  # 当前程序可注释掉
# 创建新会话，成为进程组组长
os.setsid()
# 记录守护进程pid
pid_file = os.path.abspath('./system_info_collection.pid')
f = open(pid_file, 'w+')
f.write(str(os.getpid()))
f.close()
# 注册异常退出执行函数，即守护进程异常退出删除pid文件
atexit.register(os.remove, pid_file)

while True:
    time.sleep(1)
