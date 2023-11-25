# coding=utf-8
import configparser
import datetime
import os
import platform
import re
import signal
import socket
import threading
import time
import uuid

import psutil
import requests


class SystemInfoCollection:
    # 请求参数字典
    param = {}
    # 基本配置
    config = {}

    # 通用获取mac
    def __get_mac_address(self):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])

    # 判断是否指定网卡，并返回网卡数据句柄
    def __get_net_io(self):
        if (self.config['net_key'] != ''):  # 指定网卡
            return psutil.net_io_counters(pernic=True).get(self.config['net_key'])
        else:
            return psutil.net_io_counters()

    def __init__(self):
        # 配置初始
        config_path = os.path.abspath('./config/config.ini')
        cf = configparser.ConfigParser()
        cf.read(config_path, encoding='utf-8')
        self.config['url'] = cf.get('base', 'url')
        self.config['token'] = cf.get('base', 'token')
        self.config['interval'] = int(cf.get('base', 'interval'))
        self.config['error_exit_count'] = int(cf.get('base', 'error_exit_count'))
        self.config['net_key'] = cf.get('base', 'net_key')
        if (self.config['net_key'] != ''):  # 指定网卡
            net_if_addr = psutil.net_if_addrs().get(self.config['net_key'])
            for i in net_if_addr:
                if re.match('^\d+\.\d+\.\d+\.\d+$', i.address):
                    # 系统ip
                    self.param['ip'] = i.address
                elif re.match("^([0-9a-fA-F]{2}[:\-]{1}){5}[0-9a-fA-F]{2}$", i.address):
                    # 机器mac地址
                    self.param['mac'] = i.address
        else:
            # 机器mac地址
            self.param['mac'] = self.__get_mac_address()
            # 系统ip
            self.param['ip'] = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        # 操作系统
        self.param['platform'] = platform.platform()
        # 逻辑核心数
        self.param['cpu_count'] = psutil.cpu_count()
        # 标签
        self.param['labels'] = list(filter(None, cf.get('base', 'labels').split(',')))

    def __collect(self):
        param = self.param
        # 间隔0.1秒，CPU的平均使用率
        param['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        # 内存
        memory = psutil.virtual_memory()
        # 总内存
        param['memory_total'] = memory.total
        # 可用内存
        param['memory_available'] = memory.available
        # 网络
        io = self.__get_net_io()
        b1 = io.bytes_sent
        b2 = io.bytes_recv
        # 磁盘
        io = psutil.disk_io_counters()
        c1 = io.read_bytes
        c2 = io.write_bytes
        time.sleep(1)
        # 网络
        io = self.__get_net_io()
        param['sent_sum'] = io.bytes_sent - b1
        param['recv_sum'] = io.bytes_recv - b2
        # 磁盘
        io = psutil.disk_io_counters()
        param['disk_read_sum'] = io.read_bytes - c1
        param['disk_write_sum'] = io.write_bytes - c2

        partitions = psutil.disk_partitions()
        disk_total = 0
        disk_free = 0
        disk_partitions = []
        unique_disk_devices = []
        for partition in partitions:
            if (partition.device in unique_disk_devices):
                continue  # 不重复计算已被挂载的硬盘设备
            unique_disk_devices.append(partition.device)
            disk = psutil.disk_usage(partition.mountpoint)
            disk_total = disk_total + disk.total
            disk_free = disk_free + disk.free
            disk_partitions.append({
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'total': disk.total,
                'free': disk.free
            })

        param['disk_total'] = disk_total
        param['disk_free'] = disk_free
        param['disk_partitions'] = disk_partitions

        # 请求推送
        t = threading.Thread(target=self.postData, args=(param,))
        t.start()

    # 推送数据到指定接口
    def postData(self, param):
        try:
            # 请求推送
            url = self.config['url']
            token = self.config['token']
            headers = {
                'token': token
            }
            res = requests.post(url=url, json=param, headers=headers)
            if res.status_code != 200:
                raise Exception(res.text)

            self.setErrorCount(0)
        except Exception as e:
            error_count = self.getErrorCount()
            # 异常5次，结束守护进程
            if error_count >= self.config['error_exit_count']:
                self.writeLog('程序异常，已结束守护进程')
                os.kill(os.getpid(), signal.SIGTERM)
            else:
                error_count += 1
                self.writeLog(e)
                self.setErrorCount(error_count)

    # 保存错误次数记录
    def setErrorCount(self, error_count):
        error_count_file = os.path.abspath('./runtime/error_count.cache')
        with open(error_count_file, 'w+', encoding='utf-8') as ecf:
            ecf.write(str(error_count))

    # 获取连续错误次数
    def getErrorCount(self):
        error_count_file = os.path.abspath('./runtime/error_count.cache')
        try:
            with open(error_count_file, 'r') as ecf:
                error_count = int(ecf.read())
        except FileNotFoundError:
            error_count = 0
            with open(error_count_file, 'w+', encoding='utf-8') as ecf:
                ecf.write('0')
        return error_count

    # 写日志
    def writeLog(self, content):
        log_file = os.path.abspath('./runtime/error.log')
        with open(log_file, 'a+', encoding='utf-8') as f:
            content = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(content) + "\n"
            f.write(content)

    # 启动程序
    def start(self):
        self.setErrorCount(0)
        while True:
            time.sleep(self.config['interval'] - 1)  # 这里再停滞一秒，大概3秒推送一次
            self.__collect()
