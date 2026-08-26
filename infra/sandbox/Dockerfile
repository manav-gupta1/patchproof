# Development-only sandbox image.
# Production should run the same workload contract using a hardened
# gVisor-backed runtime, non-root UID, read-only rootfs, dropped capabilities,
# seccomp, cgroups, PID limit, tmpfs workspace, and network disabled.
FROM python:3.12-slim

RUN useradd --create-home --uid 10001 runner
WORKDIR /workspace
RUN chown -R runner:runner /workspace

USER runner
ENV HOME=/home/runner
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["/bin/sh", "-lc"]
