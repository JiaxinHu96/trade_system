from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="DashboardTab",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Overview", max_length=80)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("visible_widgets", models.JSONField(blank=True, default=list)),
                ("filters", models.JSONField(blank=True, default=dict)),
                ("panel_order", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
        migrations.CreateModel(
            name="DashboardPreference",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("default_date_range", models.CharField(choices=[("all", "All"), ("7d", "7D"), ("30d", "30D"), ("mtd", "MTD"), ("ytd", "YTD")], default="all", max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("default_dashboard_tab", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="preferred_by", to="common.dashboardtab")),
            ],
        ),
    ]
