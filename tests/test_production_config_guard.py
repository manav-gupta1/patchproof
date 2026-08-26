from __future__ import annotations

import pytest
from packages.config.guard import (
    ProductionConfigurationError,
    validate_production_configuration,
)


def test_development_mode_allows_dev_settings():
    env = {
        "PATCHPROOF_ENVIRONMENT": "development",
        "PATCHPROOF_AUTH_ENABLED": "false",
        "GITHUB_WEBHOOK_SECRET": "dev-secret",
    }
    validation = validate_production_configuration(env)
    assert validation.is_production is False
    assert validation.valid is True
    assert len(validation.errors) == 0


def test_production_mode_rejects_disabled_auth():
    env = {
        "PATCHPROOF_ENVIRONMENT": "production",
        "PATCHPROOF_AUTH_ENABLED": "false",
        "GITHUB_WEBHOOK_SECRET": "secure-production-secret-1234567890",
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_PRIVATE_KEY": "pem-data",
    }
    validation = validate_production_configuration(env)
    assert validation.is_production is True
    assert validation.valid is False
    assert any("Authentication cannot be disabled in production" in e for e in validation.errors)

    with pytest.raises(ProductionConfigurationError, match="Authentication cannot be disabled in production"):
        validation.enforce()


def test_production_mode_rejects_dev_webhook_secrets():
    env = {
        "PATCHPROOF_ENVIRONMENT": "production",
        "PATCHPROOF_AUTH_ENABLED": "true",
        "GITHUB_WEBHOOK_SECRET": "dev-secret",
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_PRIVATE_KEY": "pem-data",
    }
    validation = validate_production_configuration(env)
    assert validation.is_production is True
    assert validation.valid is False
    assert any("insecure or default development secret" in e for e in validation.errors)


def test_production_mode_rejects_integration_test_flags():
    env = {
        "PATCHPROOF_ENVIRONMENT": "production",
        "PATCHPROOF_AUTH_ENABLED": "true",
        "GITHUB_WEBHOOK_SECRET": "secure-production-secret-1234567890",
        "PATCHPROOF_GITHUB_INTEGRATION_TEST": "true",
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_PRIVATE_KEY": "pem-data",
    }
    validation = validate_production_configuration(env)
    assert validation.is_production is True
    assert validation.valid is False
    assert any("PATCHPROOF_GITHUB_INTEGRATION_TEST must not be enabled in production" in e for e in validation.errors)


def test_production_mode_valid_configuration_passes():
    env = {
        "PATCHPROOF_ENVIRONMENT": "production",
        "PATCHPROOF_AUTH_ENABLED": "true",
        "GITHUB_WEBHOOK_SECRET": "production-secure-hmac-secret-abcdef123456",
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",
        "PATCHPROOF_CORS_ORIGINS": "https://app.patchproof.io,https://dashboard.patchproof.io",
    }
    validation = validate_production_configuration(env)
    assert validation.is_production is True
    assert validation.valid is True
    assert len(validation.errors) == 0


def test_production_mode_rejects_wildcard_cors():
    env = {
        "PATCHPROOF_ENVIRONMENT": "production",
        "PATCHPROOF_AUTH_ENABLED": "true",
        "GITHUB_WEBHOOK_SECRET": "production-secure-hmac-secret-abcdef123456",
        "GITHUB_APP_ID": "123456",
        "GITHUB_APP_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----",
        "PATCHPROOF_CORS_ORIGINS": "*",
    }
    validation = validate_production_configuration(env)
    assert validation.is_production is True
    assert validation.valid is False
    assert any("Wildcard CORS origin" in e for e in validation.errors)
