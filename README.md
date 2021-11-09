# 服务器信息采集工具

### 介绍

获取服务器信息，并将信息推送到指定接口，以便后续监控分析

### 特点

- 跨平台
- 简单易用

### 使用说明

1. 具备python环境
2. 安装pip
3. 执行python依赖包安装：pip install -r requirements.txt
4. 编辑config.ini文件，配置好对应的url和token

```
[base]
; 推送接口，POST请求，json格式
url = https://hello.dreamplay.top/api/test
; 该参数会添加到请求头中，键名：token
token = linzhou
```

6. 运行程序：python daemon.py

### 采集内容

```json
{
  //mac地址
  "mac": "11:11:11:11",
  //系统名称
  "platform": "Windows-10-10.0.19042-SP0",
  //服务器ip
  "ip": "172.28.48.1",
  //CPU逻辑核心数
  "cpu_count": 8,
  //总得CPU使用率
  "cpu_percent": 10.7,
  //总内存，字节，以下设计存储都是字节
  "memory_total": 12728913920,
  //可用内存
  "memory_available": 750944256,
  //网络每秒发送字节数
  "sent_sum": 23240,
  //网络每秒接收字节数
  "recv_sum": 355112,
  //磁盘每秒读字节数
  "disk_read_sum": 37599232,
  //磁盘每秒写字节数
  "disk_write_sum": 5242880,
  //磁盘总字节
  "disk_total": 755188957184,
  //磁盘总空闲字节
  "disk_free": 531016433664,
  //各个磁盘使用情况
  "disk_partitions": [
    {
      //逻辑挂载点
      "mountpoint": "C:\\",
      //总大小
      "total": 255082172416,
      //空闲大小
      "free": 106955689984
    },
    {
      "mountpoint": "D:\\",
      "total": 500106784768,
      "free": 424060743680
    }
  ]
}
```

### 开发者

1. 洲哥 <1207032539@qq.com>
