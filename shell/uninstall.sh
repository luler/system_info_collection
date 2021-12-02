#!/bin/bash

echo '正在关闭相关系统服务...'
service system_info_collection stop
echo '关闭相关系统服务完成'

echo '正在删除系统服务...'
chkconfig system_info_collection off
chkconfig --del system_info_collection
rm -f /etc/init.d/system_info_collection
echo '删除系统服务完成'

echo '正在清理代码程序代码...'
rm -rf /usr/local/system_info_collection
echo '清理代码程序代码完成'
