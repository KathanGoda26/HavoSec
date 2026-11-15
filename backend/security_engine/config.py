"""Operator-only bounded execution settings; no secrets or target-derived commands."""
import json
import os
from types import MappingProxyType
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator
from bson import ObjectId
from security_engine.policy import repository_url


class EngineSettings(BaseModel):
    model_config = ConfigDict(frozen=True, extra='forbid')
    enabled: bool = False
    poll_interval: int = Field(default=5, ge=1, le=60)
    run_timeout: int = Field(default=900, ge=60, le=3600)
    checkout_timeout: int = Field(default=120, ge=10, le=600)
    semgrep_timeout: int = Field(default=300, ge=10, le=1800)
    max_output_bytes: int = Field(default=4_000_000, ge=1024, le=8_000_000)
    max_findings: int = Field(default=500, ge=1, le=2000)
    agent_enabled: bool = False
    agent_provider: Literal['openai'] = 'openai'
    agent_model: str = Field(default='gpt-4.1-mini', pattern=r'^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$')
    agent_api_key: SecretStr | None = Field(default=None, repr=False)
    agent_timeout: int = Field(default=20, ge=1, le=60)
    max_agent_findings: int = Field(default=10, ge=0, le=50)
    max_agent_context_chars: int = Field(default=3000, ge=256, le=8000)
    remediation_timeout: int = Field(default=600, ge=30, le=1800)
    patch_max_bytes: int = Field(default=65536, ge=1024, le=1_000_000)
    patch_max_files: int = Field(default=5, ge=1, le=50)
    max_remediation_attempts: int = Field(default=1, ge=1, le=2)
    remediation_workspace_limit: int = Field(default=100_000_000, ge=1_000_000, le=2_000_000_000)
    agent_remediation_timeout: int = Field(default=30, ge=1, le=60)
    keep_workspaces: bool = False
    workspace_root: str | None = None

    @model_validator(mode='after')
    def total_budget(self):
        if self.run_timeout < self.checkout_timeout + self.semgrep_timeout:
            raise ValueError('Run timeout must cover checkout and scanner timeouts')
        return self

    @classmethod
    def from_environment(cls, environment=None):
        env = os.environ if environment is None else environment
        keys = {'enabled': 'SECURITY_WORKER_ENABLED', 'poll_interval': 'SECURITY_WORKER_POLL_INTERVAL',
                'run_timeout': 'SECURITY_RUN_TIMEOUT', 'checkout_timeout': 'REPOSITORY_CHECKOUT_TIMEOUT',
                'semgrep_timeout': 'SEMGREP_TIMEOUT', 'max_output_bytes': 'SECURITY_MAX_OUTPUT_BYTES',
                'max_findings': 'SECURITY_MAX_FINDINGS', 'agent_enabled': 'AGENT_ENABLED',
                'agent_provider': 'AGENT_PROVIDER', 'agent_model': 'AGENT_MODEL',
                'agent_api_key': 'OPENAI_API_KEY', 'agent_timeout': 'AGENT_TIMEOUT',
                'max_agent_findings': 'MAX_AGENT_FINDINGS_PER_RUN',
                'max_agent_context_chars': 'MAX_AGENT_CONTEXT_CHARS',
                'remediation_timeout': 'REMEDIATION_TIMEOUT', 'patch_max_bytes': 'PATCH_MAX_BYTES',
                'patch_max_files': 'PATCH_MAX_FILES', 'max_remediation_attempts': 'MAX_REMEDIATION_ATTEMPTS',
                'remediation_workspace_limit': 'REMEDIATION_WORKSPACE_LIMIT',
                'agent_remediation_timeout': 'AGENT_REMEDIATION_TIMEOUT',
                'keep_workspaces': 'KEEP_RUN_WORKSPACES', 'workspace_root': 'SECURITY_WORKSPACE_ROOT'}
        return cls(**{key: env[name] for key, name in keys.items() if name in env})


def repository_grants(environment=None):
    env = os.environ if environment is None else environment
    raw = env.get('SECURITY_REPOSITORY_GRANTS', '{}')
    try:
        if len(raw) > 65536:
            raise ValueError()
        data = json.loads(raw)
        if not isinstance(data, dict) or len(data) > 100:
            raise ValueError()
        result = {}
        for org, urls in data.items():
            if not ObjectId.is_valid(org) or not isinstance(urls, list) or len(urls) > 100:
                raise ValueError()
            canonical = str(ObjectId(org))
            if canonical in result:
                raise ValueError()
            result[canonical] = frozenset(repository_url(url) for url in urls)
        return MappingProxyType(result)
    except (ValueError, TypeError) as exc:
        raise ValueError('Invalid SECURITY_REPOSITORY_GRANTS configuration') from exc
