# gVisor sandbox boundary

Repository execution is now separated from the application process through a
host-side gVisor/runsc launcher boundary.

The default policy is fail-closed:

- network disabled;
- read-only sandbox root;
- bounded memory;
- bounded CPU;
- bounded process count;
- hard wall-clock timeout.

Before execution, the repository is copied into a temporary workspace and the
original checkout is never used as the writable execution directory.

`GVisorCommandRunner` is intentionally a launcher adapter, not a claim that
gVisor is installed in the development environment. Production must provide a
hardened runsc/container runtime and enforce the same policy at the runtime
layer.

The next deployment step is to run the worker itself with a dedicated service
account and mount only the temporary workspace into the sandbox.
