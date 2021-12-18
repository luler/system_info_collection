#!/bin/bash

# 设置出现异常立即终止退出
set -e

BASE_PAHT=$(cd $(dirname $0) && cd ../../ && pwd)

type=''
if [ -f /etc/redhat-release ]i; then
        type='centos'
fi
if [ `cat /etc/issue | grep -i -c ubuntu` = 1 ]; then
        type='ubuntu'
fi

case $type in

        'ubuntu')
        echo '正在检查并安装python的依赖包...'
        if [ "`command -v python3`" = "" ] || [ "`command -v pip3`" = "" ]; then
            apt install -y epel-release gcc python3 python3-pip
        fi
        pip3 install -i https://mirrors.aliyun.com/pypi/simple/ -r $BASE_PAHT/system_info_collection/requirements.txt
        echo '检查并安装python的依赖包成功'

        echo '正在复制代码程序代码...'
        cp -r $BASE_PAHT/system_info_collection /usr/local
        echo '复制代码程序代码完成'

        echo '正在初始化系统服务...'
        cp $BASE_PAHT/system_info_collection/shell/init.d/system_info_collection.sh /etc/init.d/system_info_collection
        chmod +x /etc/init.d/system_info_collection
        update-rc.d system_info_collection defaults
        echo '初始化系统服务完成'

        echo '正在启动系统服务...'
        service system_info_collection start
        echo '启动系统服务完成'
        ;;

        'centos')
        echo '正在检查并安装python的依赖包...'
        if [ "`command -v python3`" = "" ] || [ "`command -v pip3`" = "" ]; then
            yum install -y epel-release gcc python3 python3-devel
        fi
        pip3 install -i https://mirrors.aliyun.com/pypi/simple/ -r $BASE_PAHT/system_info_collection/requirements.txt
        echo '检查并安装python的依赖包成功'

        echo '正在复制代码程序代码...'
        cp -r $BASE_PAHT/system_info_collection /usr/local
        echo '复制代码程序代码完成'

        echo '正在初始化系统服务...'
        cp $BASE_PAHT/system_info_collection/shell/init.d/system_info_collection.sh /etc/init.d/system_info_collection
        chmod +x /etc/init.d/system_info_collection
        chkconfig --add system_info_collection
        chkconfig system_info_collection on
        echo '初始化系统服务完成'

        echo '正在启动系统服务...'
        if [ "`command -v service`" = "" ]; then
            yum install -y epel-release initscripts
        fi
        service system_info_collection start
        echo '启动系统服务完成'
        ;;

        *)
        echo '当前系统非centos和ubuntu系统，不支持一键安装，请自行手动安装!'
        ;;
esac
