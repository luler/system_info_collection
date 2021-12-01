#!/bin/bash

BASE_PAHT=$(cd $(dirname $0) && cd ../../ && pwd)
echo '正在复制代码程序代码...'
cp -r $BASE_PAHT/system_info_collection /usr/local
echo '复制代码程序代码完成'

echo '正在初始化系统服务...'
cp $BASE_PAHT/system_info_collection/shell/centos/system_info_collection.sh /etc/init.d/system_info_collection
chkconfig --add system_info_collection
chkconfig system_info_collection on
echo '初始化系统服务完成'

echo '正在启动系统服务...'
service system_info_collection start
echo '启动系统服务完成'
