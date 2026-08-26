# Process shutdown integration

The worker lifecycle is now connected to OS termination signals.

`SIGTERM` and `SIGINT` trigger the same idempotent graceful stop path used by
the lifecycle controller:

1. stop accepting new work
2. allow in-flight work to drain
3. wait up to the configured timeout
4. terminate the worker loop

Signal handlers can be installed and later restored, which keeps embedding
applications and tests safe.
