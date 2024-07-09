import json
from datetime import datetime
import django.db
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import redirect, render
from rest_framework.renderers import JSONRenderer
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import renderer_classes
from pymongo import MongoClient
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView

from .key_agg import key_agg
from .models import CustomUser, Project, Team, APIToken
from .query import query


def LoginUser(request):
    if request.method == "POST":
        try:
            validate_email(request.POST.get("email"))
        except ValidationError:
            messages.error(request, "Invalid email address.")
            return redirect("login")

        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user = CustomUser.objects.get(email=email)
        except django.db.models.ObjectDoesNotExist:
            messages.error(request, "Incorrect email address or password.")
            return redirect("login")
        if user is not None:
            if user.check_password(password):
                login(request, user)
                return redirect("feed")
            else:
                messages.error(request, "Incorrect email address or password.")
                return redirect("login")
    elif request.user.is_authenticated:
        return redirect("feed")
    else:
        page = "login"
        context = {
            "page": page,
        }
        return render(request, "app/_auth.html", context)


def Logout(request):
    logout(request)
    return redirect("login")


@require_http_methods(["POST", "GET"])
@login_required
def feed(request):
    if request.method == "GET":
        context = {
            "view": "feed",
        }
        return render(request, "app/_feed.html", context)


@require_http_methods(["GET"])
@login_required
def projects(request):
    projects = Project.objects.filter(team=request.user.team, deleted=False).order_by(
        "name"
    )
    context = {
        "projects": projects,
        "view": "projects",
    }
    return render(request, "app/_projects.html", context)


@require_http_methods(["GET", "POST"])
@login_required
def settings(request):
    if request.method == "GET":
        tokens = APIToken.objects.filter(team=request.user.team)
        context = {"view": "settings", "tokens": tokens}
        return render(request, "app/_settings.html", context)
    if request.method == "POST":
        request.user.first_name = request.POST.get("first-name")
        request.user.laset_name = request.POST.get("last-name")
        try:
            validate_email(request.POST.get("email"))
        except ValidationError:
            messages.error(request, "Invalid email address.")
        if (
            CustomUser.objects.filter(email=request.POST.get("email").lower()).exists()
            and request.POST.get("email").lower() != request.user.email
        ):
            messages.error(request, "Email address already in use.")
        else:
            request.user.email = request.POST.get("email").lower()
            request.user.save()
            messages.success(request, "Account information updated.")
        return redirect("settings")


@require_http_methods(["GET", "POST"])
@login_required
def team(request):
    if request.method == "GET":
        context = {
            "view": "team",
        }
        return render(request, "app/_team.html", context)
    if request.method == "POST":

        return redirect("team")


def create_project(request):
    if request.POST.get("project-name"):
        name = request.POST.get("project-name")
        projects = [
            project.name.lower()
            for project in Project.objects.filter(team=request.user.team, deleted=False)
        ]
        if request.POST.get("project-name").lower() not in projects:
            Project.objects.create(
                team=request.user.team,
                name=name,
            )
            projects = Project.objects.filter(
                team=request.user.team, deleted=False
            ).order_by("name")
            messages.success(request, f"Project '{name}' created successfully")
            context = {"projects": projects}
        else:
            projects = Project.objects.filter(
                team=request.user.team, deleted=False
            ).order_by("name")
            messages.error(request, f"A project with the name '{name}' already exists")
            context = {"projects": projects}
        if projects:
            return render(request, "app/_projects_inner.html", context)
        else:
            return render(request, "app/_projects_inner_empty.html", context)
    else:
        projects = Project.objects.filter(
            team=request.user.team, deleted=False
        ).order_by("name")
        messages.error(request, "Please provide a name for your project")
        context = {"projects": projects}
        if projects:
            return render(request, "app/_projects_inner.html", context)
        else:
            return render(request, "app/_projects_inner_empty.html", context)


def pause_project(request):
    print(request.POST.get("id"))
    if Project.objects.filter(
        id=request.POST.get("id"), team=request.user.team
    ).exists():
        project = Project.objects.get(id=request.POST.get("id"), team=request.user.team)
        project_name = project.name
        if project.paused is True:
            messages.success(request, f"Project '{project_name}' is now active")
            project.paused = False
        else:
            project.paused = True
            messages.success(request, f"Project '{project_name}' is now paused")
        project.save()
    else:
        messages.error(request, "Error pausing project. Please try again")
    projects = Project.objects.filter(team=request.user.team, deleted=False).order_by(
        "name"
    )
    context = {"projects": projects}
    if projects:
        return render(request, "app/_projects_inner.html", context)
    else:
        return render(request, "app/_projects_inner_empty.html", context)


def delete_project(request):
    if Project.objects.filter(
        id=request.POST.get("id"), team=request.user.team
    ).exists():
        project = Project.objects.get(id=request.POST.get("id"), team=request.user.team)
        project_name = project.name
        project.deleted = True
        project.save()
        projects = Project.objects.filter(
            team=request.user.team, deleted=False
        ).order_by("name")
        context = {"projects": projects}
        messages.success(request, f"Project '{project_name}' deleted successfully")
    else:
        messages.error(request, "Error deleting project. Please try again")
    if projects:
        return render(request, "app/_projects_inner.html", context)
    else:
        return render(request, "app/_projects_inner_empty.html", context)


### API ###
class health_check(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(data={"Response": "OK"}, status=status.HTTP_200_OK)


class search(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        start = datetime.now()
        initial = request.data.get("initial") == "true"
        logs, offset, has_more = query(request)

        if logs:
            print(f"Time Till Render: {datetime.now() - start}")
            return render(
                request,
                "app/_feed_inner.html",
                {
                    "logs": logs,
                    "offset": offset,
                    "has_more": has_more,
                    "query": request.data.get("query"),
                    "initial": initial,
                },
            )
        else:
            return render(request, "app/_feed_inner_empty.html")


class query_parser(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.data.get("query"):
            filters = json.loads(request.data.get("query"))
            if filters.items():
                context = {"filters": filters}
                return render(request, "app/_feed_query_item.html", context)
            else:
                return Response(status=status.HTTP_200_OK)


class update_user_timezone(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        tz = request.data.get("tz")
        if not tz:
            return Response(status=400, data={"response": "error"})
        user = request.user
        if user.timezone != tz:
            user.timezone = tz
            user.save()
            return Response(status=200, data={"response": "success"})
        return Response(status=200, data={"response": "success"})


class key_aggergation(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        keys = key_agg(request.user)
        return render(request, "app/_index_feed_add_filter.html", {"keys": keys})
