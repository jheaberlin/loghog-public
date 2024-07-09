from django.contrib import admin
from .models import CustomUser, Project, Team, APIToken

admin.site.register(CustomUser)
admin.site.register(Project)
admin.site.register(APIToken)
admin.site.register(Team)