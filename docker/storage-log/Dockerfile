#run with -v /var/log/docker-logs:/log
FROM busybox

RUN rm -rf /var/log
RUN mkdir /var/log && \
	chmod 0755 /var/log

RUN mkdir -p /var/log/{audit,cobbler,ConsoleKit,coredump,httpd,lxc,nailgun,naily,nginx,ntpstats,puppet,rabbitmq,rhsm,supervisor}

VOLUME ["/var/log"]

CMD /bin/echo storage/log I am a data-only container for Fuel && \
	cp -R /var/log /log && \
	ln -s /log /var/log
