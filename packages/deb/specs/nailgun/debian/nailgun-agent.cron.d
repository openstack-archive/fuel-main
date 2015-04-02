* * * * * root flock -w 0 -o /var/lock/agent.lock -c "/opt/nailgun/bin/agent 2>&1 | tee -a /var/log/nailgun-agent.log  | /usr/bin/logger -t nailgun-agent"
