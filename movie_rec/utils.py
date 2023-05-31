# utils.py

import json
import uuid


class UUIDEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return super(UUIDEncoder, self).default(obj)
