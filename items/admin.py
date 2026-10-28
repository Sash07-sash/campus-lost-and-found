from django.contrib import admin
from django.utils.html import format_html
from .models import Item, RecoveryRequest, ItemReport


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'report_type_badge',
        'category',
        'campus_location',
        'date_lost_or_found',
        'status_badge',
        'created_by',
        'is_flagged_badge',
        'created_at',
    )
    list_filter = ('report_type', 'status', 'category', 'is_flagged', 'date_lost_or_found', 'created_at')
    search_fields = ('title', 'description', 'campus_location', 'created_by__username', 'created_by__email')
    readonly_fields = ('created_at', 'updated_at', 'thumbnail_preview')
    date_hierarchy = 'created_at'
    actions = ['mark_as_recovered', 'unflag_items', 'flag_items']

    fieldsets = (
        ('Listing Information', {
            'fields': ('title', 'report_type', 'category', 'campus_location', 'date_lost_or_found', 'description')
        }),
        ('Visuals', {
            'fields': ('image', 'thumbnail_preview')
        }),
        ('Status & Ownership', {
            'fields': ('status', 'created_by', 'created_at', 'updated_at')
        }),
        ('Moderation', {
            'fields': ('is_flagged', 'flag_reason')
        }),
    )

    def report_type_badge(self, obj):
        color = '#dc2626' if obj.report_type == 'LOST' else '#059669'
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color, obj.get_report_type_display()
        )
    report_type_badge.short_description = 'Type'

    def status_badge(self, obj):
        colors = {
            'OPEN': '#2563eb',
            'CLAIM_PENDING': '#d97706',
            'RECOVERED': '#16a34a',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def is_flagged_badge(self, obj):
        if obj.is_flagged:
            return format_html('<span style="background-color: #ef4444; color: #fff; padding: 2px 6px; border-radius: 3px; font-size: 11px;">FLAGGED</span>')
        return format_html('<span style="color: #10b981;">Clean</span>')
    is_flagged_badge.short_description = 'Moderation'

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 150px; border-radius: 6px;" />', obj.image.url)
        return "No image uploaded"
    thumbnail_preview.short_description = 'Image Preview'

    @admin.action(description="Mark selected items as RECOVERED")
    def mark_as_recovered(self, request, queryset):
        updated = queryset.update(status='RECOVERED')
        self.message_user(request, f"{updated} items marked as RECOVERED.")

    @admin.action(description="Clear flag for selected items")
    def unflag_items(self, request, queryset):
        updated = queryset.update(is_flagged=False, flag_reason='')
        self.message_user(request, f"{updated} items unflagged.")

    @admin.action(description="Flag selected items for review")
    def flag_items(self, request, queryset):
        updated = queryset.update(is_flagged=True)
        self.message_user(request, f"{updated} items flagged for review.")


@admin.register(RecoveryRequest)
class RecoveryRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'item_link', 'requester', 'status_badge', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('item__title', 'requester__username', 'message', 'owner_notes')
    readonly_fields = ('created_at', 'updated_at')

    def item_link(self, obj):
        return format_html('<a href="/admin/items/item/{}/change/">{}</a>', obj.item.id, obj.item.title)
    item_link.short_description = 'Target Item'

    def status_badge(self, obj):
        colors = {
            'PENDING': '#d97706',
            'APPROVED': '#0284c7',
            'REJECTED': '#dc2626',
            'COMPLETED': '#16a34a',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(ItemReport)
class ItemReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'reason', 'reported_by', 'is_resolved', 'created_at')
    list_filter = ('reason', 'is_resolved', 'created_at')
    search_fields = ('item__title', 'details', 'reported_by__username')
    actions = ['mark_as_resolved']

    @admin.action(description="Mark selected reports as resolved")
    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True)
        self.message_user(request, "Reports marked as resolved.")


from .models import FAQ, SupportTicket, ErrorCode


@admin.register(ErrorCode)
class ErrorCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'http_status', 'category', 'is_active', 'updated_at')
    list_filter = ('category', 'http_status', 'is_active')
    search_fields = ('code', 'title', 'summary', 'student_explanation')
    list_editable = ('is_active',)


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('id', 'question', 'category', 'order', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number',
        'subject',
        'contact_email',
        'user',
        'related_error_code',
        'priority_badge',
        'status_badge',
        'created_at'
    )
    list_filter = ('status', 'priority', 'related_error_code', 'created_at')
    search_fields = ('ticket_number', 'subject', 'message', 'contact_email', 'user__username')
    readonly_fields = ('ticket_number', 'created_at', 'updated_at')

    def priority_badge(self, obj):
        colors = {'LOW': '#64748b', 'MEDIUM': '#0284c7', 'HIGH': '#dc2626'}
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 2px 7px; border-radius: 4px; font-size: 11px;">{}</span>',
            colors.get(obj.priority, '#64748b'), obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'

    def status_badge(self, obj):
        colors = {'OPEN': '#d97706', 'IN_PROGRESS': '#0284c7', 'RESOLVED': '#16a34a', 'CLOSED': '#64748b'}
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 2px 7px; border-radius: 4px; font-size: 11px;">{}</span>',
            colors.get(obj.status, '#64748b'), obj.get_status_display()
        )
    status_badge.short_description = 'Status'

