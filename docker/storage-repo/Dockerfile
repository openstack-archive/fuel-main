#Link /var/www/nailgun/{centos,ubuntu} to /repo/{centos,ubuntu} on invocation
FROM busybox
RUN mkdir -p /var/www/nailgun/
VOLUME /var/www/nailgun/
CMD /bin/echo storage/repo I am a data-only container for Fuel && ln -s /repo/* /var/www/nailgun/
