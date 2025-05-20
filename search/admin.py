from django.contrib import admin
from .models import SearchHistory

@admin.register(SearchHistory)
class SearchHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'query', 'result_count', 'timestamp')
    list_filter = ('user', 'timestamp')
    search_fields = ('user__username', 'query')
    readonly_fields = ('timestamp',)
    ordering = ('-timestamp',) 