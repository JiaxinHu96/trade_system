from django.db import migrations


def rebuild_trade_groups(apps, schema_editor):
    from apps.trades.services import rebuild_all_trade_groups

    rebuild_all_trade_groups()


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0002_alter_tradegroup_unique_together'),
    ]

    operations = [
        migrations.RunPython(rebuild_trade_groups, migrations.RunPython.noop),
    ]
