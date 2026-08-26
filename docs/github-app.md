# GitHub App authentication and publication

The GitHub integration is split into three boundaries:

- `GitHubAppAuth`: App JWT -> installation access token.
- `GitHubAppClient`: repository/PR operations and publication idempotency.
- `RequestsGitHubTransport`: HTTP-only transport.

Installation tokens are short-lived and are never persisted by this layer.

PR creation is idempotent. A stable marker is searched in open PR bodies before
creation. If the POST fails after the remote side may have created the PR, the
client searches again before surfacing an error. This prevents retrying a
successful-but-unknown request into duplicate PRs.

The actual JWT signing implementation should be supplied by the deployment's
approved JWT library/secret handling layer; the transport deliberately does not
store or log private keys.
