#!/bin/bash

# 设置出现异常立即终止退出
set -e

BASE_PAHT=$(cd $(dirname $0) && cd ../../ && pwd)

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

case $type in

        'debian'|'ubuntu')
        echo '正在检查并安装python的依赖包...'
        if [ "`command -v python3`" = "" ] || [ "`command -v pip3`" = "" ]; then
            apt update && apt install -y gcc python3 python3-pip python3-dev
        fi
        pip3 install -i https://mirrors.aliyun.com/pypi/simple/ -r $BASE_PAHT/requirements.txt
        echo '检查并安装python的依赖包成功'

        echo '正在复制代码程序代码...'
        cp -r $BASE_PAHT /usr/local/system_info_collection
        echo '复制代码程序代码完成'

        # 创建 config.ini 配置文件（如果不存在）
        if [ ! -f /usr/local/system_info_collection/config.ini ]; then
                if [ -f $BASE_PAHT/config.ini.example ]; then
                        cp $BASE_PAHT/config.ini.example /usr/local/system_info_collection/config.ini
                fi
        fi

        # 优先使用 systemd（Debian 8+/Ubuntu 15.04+）
        if [ -d /lib/systemd/system ]; then
                echo '正在初始化systemd系统服务...'
                cat > /lib/systemd/system/system_info_collection.service <<EOF
[Unit]
Description=System Info Collection Service
After=network.target

[Service]
Type=forking
WorkingDirectory=/usr/local/system_info_collection
ExecStart=/usr/bin/python3 /usr/local/system_info_collection/daemon.py start
ExecStop=/usr/bin/python3 /usr/local/system_info_collection/daemon.py stop
Restart=on-failure
User=root

[Install]
WantedBy=multi-user.target
EOF
                systemctl daemon-reload
                systemctl enable system_info_collection
                systemctl start system_info_collection
                echo '初始化systemd系统服务完成'
        else
                echo '正在初始化系统服务...'
                cp $BASE_PAHT/shell/init.d/system_info_collection.sh /etc/init.d/system_info_collection
                chmod +x /etc/init.d/system_info_collection
                update-rc.d system_info_collection defaults 2>/dev/null || update-rc.d system_info_collection start 20 2 3 4 5 . stop 20 0 1 6 .
                echo '初始化系统服务完成'

                echo '正在启动系统服务...'
                service system_info_collection start
                echo '启动系统服务完成'
        fi
        ;;

        'centos')
        echo '正在检查并安装python的依赖包...'
        if [ "`command -v python3`" = "" ] || [ "`command -v pip3`" = "" ]; then
            yum install -y epel-release gcc python3 python3-devel
        fi
        pip3 install -i https://mirrors.aliyun.com/pypi/simple/ -r $BASE_PAHT/requirements.txt
        echo '检查并安装python的依赖包成功'

        echo '正在复制代码程序代码...'
        cp -r $BASE_PAHT /usr/local/system_info_collection
        echo '复制代码程序代码完成'

        # 创建 config.ini 配置文件（如果不存在）
        if [ ! -f /usr/local/system_info_collection/config.ini ]; then
                if [ -f $BASE_PAHT/config.ini.example ]; then
                        cp $BASE_PAHT/config.ini.example /usr/local/system_info_collection/config.ini
                fi
        fi

        echo '正在初始化系统服务...'
        cp $BASE_PAHT/shell/init.d/system_info_collection.sh /etc/init.d/system_info_collection
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
        echo '当前系统非centos、debian和ubuntu系统，不支持一键安装，请自行手动安装!'
        ;;
esac
