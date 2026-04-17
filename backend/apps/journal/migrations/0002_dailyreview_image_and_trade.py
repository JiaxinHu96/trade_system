from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0001_initial'),
        ('journal', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dailyreview',
            name='review_date',
            field=models.DateField(db_index=True, default=django.utils.timezone.localdate),
        ),
        migrations.AlterModelOptions(
            name='dailyreview',
            options={'ordering': ['-review_date', '-updated_at']},
        ),
        migrations.AddField(
            model_name='dailyreview',
            name='image_url',
            field=models.CharField(blank=True, default='', max_length=500),
        ),
        migrations.AddField(
            model_name='dailyreview',
            name='related_trade_group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='daily_reviews', to='trades.tradegroup'),
        ),
        migrations.AlterField(
            model_name='dailyreview',
            name='review_date',
            field=models.DateField(db_index=True, default=django.utils.timezone.localdate),
        ),
    ]
