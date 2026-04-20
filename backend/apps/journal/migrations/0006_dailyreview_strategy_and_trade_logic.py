from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0005_remove_tradejournal_tv_snapshot_url'),
    ]

    operations = [
        migrations.AddField(
            model_name='dailyreview',
            name='strategy',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
        migrations.AddField(
            model_name='dailyreview',
            name='thesis',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='dailyreview',
            name='entry_logic',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='dailyreview',
            name='exit_logic',
            field=models.TextField(blank=True, default=''),
        ),
    ]
