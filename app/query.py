import json
import re
from datetime import datetime
from uuid import UUID
from dotenv import load_dotenv
import os

from bson.json_util import dumps
from pymongo import MongoClient

from .models import Project
from .convert_tz import convert_tz
from .type import convert_type

client = MongoClient(
    os.getenv("MONGOURL"),
)
db = client.logDB
collection = db["logs"]


def query(request) -> dict:

    projects = Project.objects.filter(team=request.user.team, deleted=False)
    user_query = json.loads(request.POST.get("query"))
    offset, limit = (
        int(request.data.get("offset", 0)),
        min(int(request.data.get("limit", 250)), 250),
    )
    sort, direction = (
        request.data.get("sort", "created"),
        request.data.get("direction", -1),
    )
    query = {k: parser(v) for k, v in user_query.items()}

    inner_args = ["$gte", "$lte", "$gt", "$lt", "$not", "$exists"]

    for key, value in query.items():
        for arg in inner_args:
            if arg in value:
                if arg == "$not":
                    for k, v in value["$not"].items():
                        value["$not"][k] = convert_type(v, request.user.timezone)
                else:
                    for k, v in value.items():
                        value[k] = convert_type(v, request.user.timezone)
            else:
                query[key] = convert_type(value, request.user.timezone)

    if "project_id" in query:
        print(query["project_id"])
        query["project_id"] = handle_projects(query["project_id"], projects)
    else:
        query["project_id"] = {"$in": [str(project.id) for project in projects]}
    logs_cursor = collection.find(query).limit(limit).skip(offset).sort(sort, direction)
    logs_binary = dumps(list(logs_cursor))
    logs_json = format(json.loads(logs_binary), projects, request.user.timezone)
    has_more = collection.count_documents(query, skip=offset + limit, limit=1) > 0

    print(query)

    return logs_json, offset + limit, has_more


def parser(value) -> str | dict:
    operators = {
        ">": "$gt",
        "<": "$lt",
        ">=": "$gte",
        "<=": "$lte",
        "!=": "$ne",
        "IN": in_parser,
        "ICONTAINS": icontains_parser,
        "CONTAINS": contains_parser,
        "NOT ICONTAINS": not_icontains_parser,
        "NOT CONTAINS": not_contains_parser,
    }

    if re.match(r"^NOT EXISTS", value) and len(value.split()) == 2:
        return {"$exists": False}
    elif re.match(r"^EXISTS", value) and len(value.split()) == 1:
        return {"$exists": True}
    else:
        for op, func in operators.items():
            if len(value.split()) > 1:
                if callable(func) and re.match(rf"^{op}", value):
                    return func(value)
                elif re.match(rf"^{op}", value):
                    print(op)
                    return {func: re.sub(rf"^{op}", "", value).strip()}
    return value.strip()


def in_parser(value) -> dict:
    value = value.split(" to ")
    return {"$gte": value[0].replace("IN", "").strip(), "$lte": value[1].strip()}


def icontains_parser(value) -> dict:
    return {
        "$regex": value.replace("ICONTAINS", "").strip(),
        "$options": "i",
    }


def contains_parser(value) -> dict:
    return {"$regex": re.sub(r"^CONTAINS", "", value, count=1).strip()}


def not_icontains_parser(value) -> dict:
    return {
        "$not": {
            "$regex": value.replace("NOT ICONTAINS", "").strip(),
            "$options": "i",
        }
    }


def not_contains_parser(value) -> dict:
    return {"$not": {"$regex": value.replace("NOT CONTAINS", "").strip()}}


def handle_projects(value, projects) -> dict:
    projects = [str(project.id) for project in projects]
    if value in projects:
        return value
    else:
        return {"$in": projects}


def format(logs, projects, timezone):
    projects = {proj.id: proj.name for proj in projects}
    for log in logs:
        log["id"] = log["_id"]["$oid"]
        log["project_name"] = projects.get(UUID(log["project_id"]))
        log["created"] = convert_tz(
            datetime.fromisoformat(log["created"]["$date"].replace("Z", "+00:00")),
            timezone,
        )
        del log["_id"]
    return logs
