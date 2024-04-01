FROM debian:stable-20240211-slim

# Install Moulti:
COPY README.md pyproject.toml setup.py /tmp/moulti
COPY src/moulti /tmp/moulti/src/moulti
ENV PIPX_HOME=/opt/pipx PIPX_BIN_DIR=/usr/local/bin PIPX_MAN_DIR=/usr/local/share/man
RUN unlink /etc/apt/apt.conf.d/docker-clean && \
    apt update && \
    apt install --no-install-recommends -y pipx xclip && \
    pipx install /tmp/moulti && \
    mkdir /export && \
    rm -rf /tmp/moulti /root/.cache && \
    rm -rf /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin /var/lib/apt/lists/deb*

# Install the demo script:
COPY examples/upgrade-system.bash examples/moulti-functions.bash /root

# Required as upgrade-system.bash sources "moulti-functions.bash":
WORKDIR /root

ENV TERM=xterm-256color COLORTERM=truecolor MOULTI_SAVE_PATH=/export DISPLAY=:0

# ENTRYPOINT ["./upgrade-system.bash"] works but setting moulti as entrypoint makes it easier to play with Moulti itself:
ENTRYPOINT ["/usr/local/bin/moulti"]
CMD ["run", "./upgrade-system.bash"]
