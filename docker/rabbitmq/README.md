docker-rsyslog
===================

Fuel docker-rsyslog container


```bash
cp /etc/astute.yaml ./

# build
docker build -t fuel/rabbitmq ./

# run AFTER storage-puppet and storage-log

docker run \
  -h $(hostname -f) \
  -p 5672:5672 \
  -p 4369:4369 \
  -p 15672:15672 \
  -p 61613:61613 \
  -d -t \
  --volumes-from storage-puppet \
  --volumes-from storage-log \
  --name fuel-rabbitmq \
  fuel/rabbitmq

```
