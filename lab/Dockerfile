FROM frrouting/frr:latest
RUN apk add --no-cache openssh && adduser -D netadmin && echo "netadmin:lab12345" | chpasswd && addgroup netadmin frrvty && addgroup netadmin frr
ENTRYPOINT []
CMD ["/bin/sh", "-c", "ssh-keygen -A && /usr/sbin/sshd && exec /sbin/tini -- /usr/lib/frr/docker-start"]
