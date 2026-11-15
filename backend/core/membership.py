"""Compatibility reader: ambiguous legacy tenant aliases never grant access."""
from bson import ObjectId

MEMBERSHIP_FIELDS = ('organizationId', 'organization_id', 'clientId')


def membership_value(account):
    values = []
    for key in MEMBERSHIP_FIELDS:
        value = account.get(key)
        if value is None or value == '':
            continue
        if not isinstance(value, (str, ObjectId)):
            return None, 'invalid'
        value = str(value)
        if ObjectId.is_valid(value):
            value = str(ObjectId(value))
        values.append(value)
    if not values:
        return None, 'missing'
    if len(set(values)) != 1:
        return None, 'conflicting'
    return values[0], 'assigned'
