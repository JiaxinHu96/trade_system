from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("journal", "0004_tradejournal_tv_snapshot_url"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="tradejournal",
            name="tv_snapshot_url",
        ),
    ]
