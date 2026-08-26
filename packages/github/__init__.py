from packages.github.app import GitHubAppConfig, GitHubWebhookHandler, GitHubCheckPayload
from packages.github.auth import (
    GitHubAppAuth,
    GitHubAuthError,
    InstallationToken,
    GitHubAppCredentials,
    create_app_jwt,
    request_installation_token,
    sanitize_secret_text,
)
from packages.github.client import GitHubAppClient, PullRequestRef
from packages.github.fake_client import FakeGitHubClient
from packages.github.publisher import GitHubPublisher, PublicationRejected
from packages.github.transport import (
    GitHubAPIError,
    GitHubAuthError,
    GitHubPermissionError,
    GitHubNotFoundError,
    GitHubConflictError,
    GitHubUnprocessableError,
    GitHubRateLimitError,
    GitHubServerError,
    GitHubTransientError,
    GitHubAuthenticationError,
    GitHubAuthorizationError,
    RequestsGitHubTransport,
)


class PullRequestPublisher(GitHubPublisher):
    async def publish(self, **kwargs):
        return super().publish(**kwargs)


__all__ = [
    "GitHubAppConfig",
    "GitHubWebhookHandler",
    "GitHubCheckPayload",
    "GitHubAppAuth",
    "GitHubAuthError",
    "InstallationToken",
    "GitHubAppCredentials",
    "create_app_jwt",
    "request_installation_token",
    "sanitize_secret_text",
    "GitHubAppClient",
    "PullRequestRef",
    "GitHubAPIError",
    "GitHubPermissionError",
    "GitHubNotFoundError",
    "GitHubConflictError",
    "GitHubUnprocessableError",
    "GitHubRateLimitError",
    "GitHubServerError",
    "GitHubTransientError",
    "GitHubAuthenticationError",
    "GitHubAuthorizationError",
    "RequestsGitHubTransport",
    "FakeGitHubClient",
    "GitHubPublisher",
    "PublicationRejected",
    "PullRequestPublisher",
]
