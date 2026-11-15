"""Strict IDs for new domain records; legacy IDs are not rewritten."""
from bson import ObjectId
from fastapi import HTTPException


def object_id(value) -> ObjectId:
    if not isinstance(value, (str, ObjectId)) or not ObjectId.is_valid(value):
        raise HTTPException(status_code=404, detail='Resource not found')
    return ObjectId(value)


def canonical_id(value) -> str:
    return str(object_id(value))
