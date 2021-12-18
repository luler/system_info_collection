#!/bin/sh
# chkconfig: 2345 55 25
# For CentOS/Redhat run: 'chkconfig --add system_info_collection' and 'chkconfig system_info_collection on'

BASE_PAHT=/usr/local/system_info_collection

case "$1" in
start)
  cd $BASE_PAHT && python3 daemon.py start
  ;;

stop)
  cd $BASE_PAHT && python3 daemon.py stop
  ;;

status)
  cd $BASE_PAHT && python3 daemon.py status
  ;;

restart)
  cd $BASE_PAHT && python3 daemon.py restart
  ;;

*)
  echo "Usage: $0 {start|stop|restart|status}"
  exit 1
  ;;
esac
