#!/bin/bash

set -x

type=''
if [ -f /etc/redhat-release ]i; then
        type='centos'
fi
if [ `cat /etc/issue | grep -i -c ubuntu` = 1 ]; then
        type='ubuntu'
fi

echo '正在关闭相关系统服务...'
service system_info_collection stop
echo '关闭相关系统服务完成'

case $type in

        'ubuntu')
        echo '正在删除系统服务...'
        update-rc.d -f system_info_collection remove
        rm -f /etc/init.d/system_info_collection
        echo '删除系统服务完成'
        ;;

        'centos')
        echo '正在删除系统服务...'
        chkconfig system_info_collection off
        chkconfig --del system_info_collection
        rm -f /etc/init.d/system_info_collection
        echo '删除系统服务完成'
        ;;

        *)
        echo '当前系统非centos和ubuntu系统，不支持一键卸载，请自行手动卸载!'
        ;;
esac

echo '正在清理代码程序代码...'
rm -rf /usr/local/system_info_collection
echo '清理代码程序代码完成'
