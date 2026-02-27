#!/bin/bash

set -e

type=''
if [ -f /etc/redhat-release ]; then
        type='centos'
fi
if [ -f /etc/debian_version ] || [ `cat /etc/issue 2>/dev/null | grep -i -c -E 'debian|ubuntu|mint' || echo 0` -gt 0 ]; then
        if [ -f /etc/debian_version ]; then
                type='debian'
        else
                type='ubuntu'
        fi
fi

echo '正在关闭相关系统服务...'
service system_info_collection stop 2>/dev/null || true
echo '关闭相关系统服务完成'

case $type in

        'debian'|'ubuntu')
        # 优先使用 systemd
        if [ -d /lib/systemd/system ]; then
                echo '正在删除systemd系统服务...'
                systemctl stop system_info_collection 2>/dev/null || true
                systemctl disable system_info_collection 2>/dev/null || true
                rm -f /lib/systemd/system/system_info_collection.service
                systemctl daemon-reload
                echo '删除systemd系统服务完成'
        else
                echo '正在删除系统服务...'
                update-rc.d -f system_info_collection remove 2>/dev/null || true
                rm -f /etc/init.d/system_info_collection
                echo '删除系统服务完成'
        fi
        ;;

        'centos')
        echo '正在删除系统服务...'
        chkconfig system_info_collection off 2>/dev/null || true
        chkconfig --del system_info_collection 2>/dev/null || true
        rm -f /etc/init.d/system_info_collection
        echo '删除系统服务完成'
        ;;

        *)
        echo '当前系统非centos、ubuntu和debian系统，不支持一键卸载，请自行手动卸载!'
        ;;
esac

echo '正在清理代码程序代码...'
rm -rf /usr/local/system_info_collection
echo '清理代码程序代码完成'
