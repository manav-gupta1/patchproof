FROM semgrep/semgrep:latest
WORKDIR /workspace
ENTRYPOINT ["semgrep"]
