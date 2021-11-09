# coding=utf-8
import datetime
import uuid
import psutil
import time
import socket
import platform
import requests
import configparser
import os
import signal


class SystemInfoCollection:
    # 错误次数
    error_count = 0
    # 请求参数字典
    param = {}

    def __get_mac_address(self):
        mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        return ":".join([mac[e:e + 2] for e in range(0, 11, 2)])

    def __init__(self):
        # 机器mac地址
        self.param['mac'] = self.__get_mac_address()
        # 操作系统
        self.param['platform'] = platform.platform()
        # 系统ip
        self.param['ip'] = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
        # 逻辑核心数
        self.param['cpu_count'] = psutil.cpu_count()

    def __collect(self):
        # 间隔0.1秒，CPU的平均使用率
        self.param['cpu_percent'] = psutil.cpu_percent(interval=0.1)
        # 内存
        memory = psutil.virtual_memory()
        # 总内存
        self.param['memory_total'] = memory.total
        # 可用内存
        self.param['memory_available'] = memory.available
        # 网络
        io = psutil.net_io_counters()
        b1 = io.bytes_sent
        b2 = io.bytes_recv
        # 磁盘
        io = psutil.disk_io_counters()
        c1 = io.read_bytes
        c2 = io.write_bytes
        time.sleep(1)
        # 网络
        io = psutil.net_io_counters()
        self.param['sent_sum'] = io.bytes_sent - b1
        self.param['recv_sum'] = io.bytes_recv - b2
        # 磁盘
        io = psutil.disk_io_counters()
        self.param['disk_read_sum'] = io.read_bytes - c1
        self.param['disk_write_sum'] = io.write_bytes - c2

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

        self.param['disk_total'] = disk_total
        self.param['disk_free'] = disk_free
        self.param['disk_partitions'] = disk_partitions

        # 请求推送
        config_path = os.path.abspath('./config/config.ini')
        cf = configparser.ConfigParser()
        cf.read(config_path, encoding='utf-8')
        url = cf.get('base', 'url')
        token = cf.get('base', 'token')
        headers = {
            'token': token
        }
        res = requests.post(url=url, json=self.param, headers=headers)
        if res.status_code != 200:
            raise Exception(res.text.encode('utf-8'))

    def start(self):
        while True:
            try:
                time.sleep(2)  # 这里再停滞一秒，大概3秒推送一次
                self.__collect()
                # 执行成功，恢复
                self.error_count = 0
            except Exception as e:
                log_file = os.path.abspath('./runtime/error.log')
                # 异常5次，结束守护进程
                if self.error_count >= 5:
                    with open(log_file, 'a+') as f:
                        content = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' 程序异常，已结束守护进程' + "\n"
                        f.write(content)
                    os.kill(os.getpid(), signal.SIGKILL)
                else:
                    self.error_count += 1
                    with open(log_file, 'a+') as f:
                        content = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' ' + str(e) + "\n"
                        f.write(content)
