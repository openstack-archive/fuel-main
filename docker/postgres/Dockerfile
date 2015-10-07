# fuel/postgres

FROM fuel/centos
MAINTAINER Aleksandr Didenko adidenko@mirantis.com

ENV DOCKER_PORT _PORT_

ADD etc /etc
ADD start.sh /usr/local/bin/
ADD setup.sh /usr/local/bin/
ADD start-container.service /etc/systemd/system/

RUN chmod +x /usr/local/bin/{setup,start}.sh

EXPOSE 5432

CMD ["/usr/lib/systemd/systemd"]
