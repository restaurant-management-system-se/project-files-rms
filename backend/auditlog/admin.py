from django.contrib import admin
from accounts.admin import RestaurantAdminOnly
from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(RestaurantAdminOnly,admin.ModelAdmin):
    list_display=['id','actor_id','action','object_type','object_id','occurred_at']
    list_filter=['action','object_type']
    readonly_fields=['actor','action','object_type','object_id','occurred_at','source_override']

    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
