"""Health check endpoint — GET /api/health"""

import json


def handler(request):
    return {
        "statusCode": 200,
        "body": json.dumps({"status": "ok", "service": "instagram-avatar-pipeline"}),
    }
