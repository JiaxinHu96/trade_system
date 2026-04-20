from django.db import models


class DashboardTab(models.Model):
    name = models.CharField(max_length=80, default="Overview")
    sort_order = models.PositiveIntegerField(default=0)
    visible_widgets = models.JSONField(default=list, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    panel_order = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return self.name


class DashboardPreference(models.Model):
    DATE_RANGE_CHOICES = [
        ("all", "All"),
        ("7d", "7D"),
        ("30d", "30D"),
        ("mtd", "MTD"),
        ("ytd", "YTD"),
    ]

    default_dashboard_tab = models.ForeignKey(
        DashboardTab, null=True, blank=True, on_delete=models.SET_NULL, related_name="preferred_by"
    )
    default_date_range = models.CharField(max_length=10, choices=DATE_RANGE_CHOICES, default="all")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_solo(cls):
        obj = cls.objects.first()
        if obj:
            return obj
        return cls.objects.create()

    def __str__(self):
        return "Dashboard Preferences"


class StrategyOption(models.Model):
    name = models.CharField(max_length=80, unique=True)
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["sort_order", "name", "id"]

    def __str__(self):
        return self.name
