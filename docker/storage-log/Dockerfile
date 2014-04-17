#run with -v /var/log/docker-logs:/log
FROM busybox
RUN rm -rf /var/log
RUN mkdir /var/log && chmod 0755 /var/log
RUN for dir in audit cobbler ConsoleKit coredump httpd lxc nailgun naily nginx ntpstats puppet rabbitmq rhsm supervisor ; do mkdir -p /var/log/$dir; done
VOLUME ["/var/log"]
CMD /bin/echo storage/log I am a data-only container for Fuel && cp -R /var/log /log && ln -s /log /var/log
