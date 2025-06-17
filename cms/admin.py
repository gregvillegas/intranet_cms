from django.contrib import admin
from .models import Department, Announcement, SharedFile, UserProfile

admin.site.register(Department)
admin.site.register(Announcement)
admin.site.register(SharedFile)
admin.site.register(UserProfile)
#@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department')
    search_fields = ('user__username', 'department__name')

