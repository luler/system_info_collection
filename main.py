# coding=utf-8
import psutil as psutil
import time
import socket
import platform
import requests
import configparser
import os

param = {}
# 操作系统
param['platform'] = platform.platform()
# 系统ip
param['ip'] = socket.gethostbyname(socket.getfqdn(socket.gethostname()))
# 逻辑核心数
param['cpu_count'] = psutil.cpu_count()
# 间隔0.1秒，CPU的平均使用率
param['cpu_percent'] = psutil.cpu_percent(interval=0.1)
# 内存
memory = psutil.virtual_memory()
# 总内存
param['memory_total'] = memory.total
param['memory_available'] = memory.available

io = psutil.net_io_counters()
b1 = io.bytes_sent
b2 = io.bytes_recv
time.sleep(1)
io = psutil.net_io_counters()
param['sent_sum'] = io.bytes_sent - b1
param['recv_sum'] = io.bytes_recv - b2
# 磁盘
io = psutil.disk_io_counters()
b1 = io.read_bytes
b2 = io.write_bytes
time.sleep(1)
io = psutil.disk_io_counters()
param['disk_read_sum'] = io.read_bytes - b1
param['disk_write_sum'] = io.write_bytes - b2

partitions = psutil.disk_partitions()
disk_total = 0
disk_free = 0
disk_partitions = []
for partition in partitions:
    disk = psutil.disk_usage(partition.mountpoint)
    disk_total = disk_total + disk.total
    disk_free = disk_free + disk.free
    disk_partitions.append({'mountpoint': partition.mountpoint, 'total': disk.total, 'free': disk.free})

param['disk_total'] = disk_total
param['disk_free'] = disk_free
param['disk_partitions'] = disk_partitions

# 请求推送
config_path = os.path.abspath('config.ini')
cf = configparser.ConfigParser()
cf.read(config_path, encoding='utf-8')
url = cf.get('base', 'url')
token = cf.get('base', 'token')
headers = {
    'token': token
}
res = requests.post(url=url, json=param, headers=headers)
if res.status_code != 200:
    raise Exception(res.text)
