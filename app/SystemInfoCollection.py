# coding=utf-8
import configparser
import datetime
import os
import platform
import queue
import re
import signal
import socket
import threading
import time
import uuid

import psutil
import requests


class SystemInfoCollection:
    def __init__(self):
        # --- 配置加载 ---
        config_path = os.path.abspath('./config/config.ini')
        cf = configparser.ConfigParser()
        cf.read(config_path, encoding='utf-8')
        self.config = {
            'url': cf.get('base', 'url'),
            'token': cf.get('base', 'token'),
            'interval': int(cf.get('base', 'interval')),
            'error_exit_count': int(cf.get('base', 'error_exit_count')),
            'net_key': cf.get('base', 'net_key')
        }

        # --- 生产者-消费者模式所需组件 ---
        self.data_queue = queue.Queue()  # 用于存放采集数据的线程安全队列
        self.stop_event = threading.Event()  # 用于通知工作线程停止的事件

        # --- 状态化数据，用于计算速率 ---
        self.last_collect_time = None
        self.last_net_io = None
        self.last_disk_io = None

        # --- 内存中的错误计数器 ---
        self.error_count = 0

        # --- 基础静态信息采集 ---
        self.param = {}
        self._initialize_static_params()

    def _initialize_static_params(self):
        """仅在初始化时采集一次的静态信息"""
        # MAC 和 IP 地址
        if self.config['net_key']:
            net_if_addrs = psutil.net_if_addrs().get(self.config['net_key'], [])
            for addr in net_if_addrs:
                if addr.family == socket.AF_INET:
                    self.param['ip'] = addr.address
                elif addr.family == psutil.AF_LINK:
                    self.param['mac'] = addr.address
        if not self.param.get('mac'):
            mac_int = uuid.getnode()
            self.param['mac'] = ':'.join(re.findall('..', '%012x' % mac_int))
        if not self.param.get('ip'):
            try:
                self.param['ip'] = socket.gethostbyname(socket.gethostname())
            except socket.gaierror:
                self.param['ip'] = '127.0.0.1'

        self.param['platform'] = platform.platform()
        self.param['cpu_count'] = psutil.cpu_count()

        cf = configparser.ConfigParser()
        cf.read(os.path.abspath('./config/config.ini'), encoding='utf-8')
        self.param['labels'] = list(filter(None, cf.get('base', 'labels').split(',')))

    def __get_net_io(self):
        """根据配置获取网络IO计数器"""
        if self.config['net_key']:
            return psutil.net_io_counters(pernic=True).get(self.config['net_key'])
        return psutil.net_io_counters()

    def _collect(self):
        """
        非阻塞式数据采集。
        计算网络和磁盘速率需要前后两次数据对比，此方法通过保存上一次的状态来实现。
        """
        current_time = time.time()
        param = self.param.copy()

        # CPU
        param['cpu_percent'] = psutil.cpu_percent(interval=None)  # 非阻塞

        # 内存
        memory = psutil.virtual_memory()
        param['memory_total'] = memory.total
        param['memory_available'] = memory.available

        # 磁盘分区 (使用set优化去重)
        partitions = psutil.disk_partitions()
        disk_total, disk_free = 0, 0
        disk_partitions_list = []
        unique_disk_devices = set()
        for partition in partitions:
            if partition.device in unique_disk_devices:
                continue
            unique_disk_devices.add(partition.device)
            try:
                disk_usage = psutil.disk_usage(partition.mountpoint)
                disk_total += disk_usage.total
                disk_free += disk_usage.free
                disk_partitions_list.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'total': disk_usage.total,
                    'free': disk_usage.free
                })
            except (FileNotFoundError, PermissionError):
                continue  # 忽略无法访问的挂载点
        param['disk_total'] = disk_total
        param['disk_free'] = disk_free
        param['disk_partitions'] = disk_partitions_list

        # 网络和磁盘速率 (状态化计算)
        current_net_io = self.__get_net_io()
        current_disk_io = psutil.disk_io_counters()

        if self.last_collect_time and current_net_io and self.last_net_io and current_disk_io and self.last_disk_io:
            time_delta = current_time - self.last_collect_time
            if time_delta > 0:
                param['sent_sum'] = int((current_net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta)
                param['recv_sum'] = int((current_net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta)
                param['disk_read_sum'] = int((current_disk_io.read_bytes - self.last_disk_io.read_bytes) / time_delta)
                param['disk_write_sum'] = int(
                    (current_disk_io.write_bytes - self.last_disk_io.write_bytes) / time_delta)

                # 数据采集完成，放入队列
                self.data_queue.put(param)

        # 更新状态以备下次计算
        self.last_collect_time = current_time
        self.last_net_io = current_net_io
        self.last_disk_io = current_disk_io

    def _post_data_worker(self):
        """消费者工作线程：从队列获取数据并上报"""
        while not self.stop_event.is_set():
            try:
                # 阻塞等待，直到队列中有数据或超时
                param = self.data_queue.get(timeout=1)

                try:
                    res = requests.post(
                        url=self.config['url'],
                        json=param,
                        headers={'token': self.config['token']},
                        timeout=10  # 设置请求超时
                    )
                    if res.status_code != 200:
                        raise Exception(f"HTTP Status {res.status_code}: {res.text}")

                    # 请求成功，重置错误计数器
                    self.error_count = 0
                except Exception as e:
                    self.error_count += 1
                    self.write_log(f"Data post failed: {e}")
                    if self.error_count >= self.config['error_exit_count']:
                        self.write_log("Error count exceeded limit. Shutting down.")
                        # 发送SIGTERM信号给自身进程，以便被守护进程管理器捕获
                        os.kill(os.getpid(), signal.SIGTERM)
                        break

                self.data_queue.task_done()

            except queue.Empty:
                # 队列为空时超时，继续循环检查 stop_event
                continue

    def write_log(self, content):
        log_file = os.path.abspath('./runtime/error.log')
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(f"{timestamp} {content}\n")

    def start(self):
        """启动生产者（主循环）和消费者（工作线程）"""
        self.error_count = 0  # 启动时重置

        # 启动消费者工作线程
        worker_thread = threading.Thread(target=self._post_data_worker, daemon=True)
        worker_thread.start()

        self.write_log("System Info Collector started.")

        # 首次采集，初始化速率计算基线
        self._collect()

        # 生产者主循环
        while not self.stop_event.is_set():
            loop_start_time = time.time()
            self._collect()
            elapsed_time = time.time() - loop_start_time

            sleep_time = self.config['interval'] - elapsed_time
            if sleep_time > 0:
                # 使用事件的wait方法进行可中断的睡眠
                self.stop_event.wait(sleep_time)

    def stop(self):
        """优雅地停止服务"""
        self.write_log("Stopping System Info Collector...")
        self.stop_event.set()  # 通知所有线程停止
        # 等待队列中的任务完成
        self.data_queue.join()
