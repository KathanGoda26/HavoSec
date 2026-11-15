import hashlib
import hmac

import pytest

from integrations.github.webhooks import (GitHubWebhookError, aggregate_checks,
                                           check_state, validate_delivery,
                                           verify_signature)


SECRET = 'test-webhook-secret-that-is-at-least-32-bytes'
BODY = b'{"zen":"security"}'


def signature(body=BODY):
    return 'sha256=' + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_and_delivery_are_accepted():
    verify_signature(BODY, signature(), SECRET)
    assert validate_delivery('123e4567-e89b-12d3-a456-426614174000') == '123e4567-e89b-12d3-a456-426614174000'


@pytest.mark.parametrize('value', [None, '', 'sha1=bad', 'sha256=' + '0' * 64])
def test_missing_malformed_or_invalid_signature_is_rejected(value):
    with pytest.raises(GitHubWebhookError):
        verify_signature(BODY, value, SECRET)


@pytest.mark.parametrize(('status', 'conclusion', 'expected'), [
    ('queued', None, 'pending'), ('in_progress', None, 'pending'),
    ('completed', 'success', 'passing'), ('completed', 'neutral', 'passing'),
    ('completed', 'failure', 'failing'), ('completed', 'timed_out', 'failing'),
    ('completed', None, 'unknown'),
])
def test_check_state_is_conservative(status, conclusion, expected):
    assert check_state(status, conclusion) == expected


def test_check_aggregation_never_claims_success_while_pending_or_failing():
    assert aggregate_checks({}) == 'unknown'
    assert aggregate_checks({'a': 'passing', 'b': 'pending'}) == 'pending'
    assert aggregate_checks({'a': 'passing', 'b': 'failing'}) == 'failing'
    assert aggregate_checks({'a': 'passing', 'b': 'passing'}) == 'passing'
