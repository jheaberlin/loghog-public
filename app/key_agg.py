from pymongo import MongoClient
from .models import Project
from django.core.cache import cache
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

client = MongoClient(
    os.getenv("MONGOURL"),
)
db = client.logDB
collection = db["logs"]


def key_agg(user):
    projects = Project.objects.filter(team=user.team, deleted=False)

    p_array = []

    for p in projects:
        p_array.append(str(p.id))

    keys = cache.get(str(user.team.id))

    if keys:
        return keys

    else:
        start = datetime.now()
        pipeline = [
            {"$match": {"project_id": {"$in": p_array}}},
            {"$sort": {"created": -1}},
            # {"$limit": 10000},
            {"$project": {"arrayofkeyvalue": {"$objectToArray": "$context"}}},
            {"$unwind": "$arrayofkeyvalue"},
            {"$group": {"_id": "$arrayofkeyvalue.k"}},
        ]

        keys = list(collection.aggregate(pipeline))

        for key in keys:
            key["name"] = key["_id"]
            del key["_id"]

        cache.set(str(user.team.id), keys, 3600)
        print(f"Key arg took {datetime.now() - start}")
        return keys
