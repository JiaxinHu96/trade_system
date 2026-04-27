from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0004_tradematchedlot'),
    ]

    operations = [
        migrations.AddField(
            model_name='tradegroup',
            name='is_soft_deleted',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AddField(
            model_name='tradegroup',
            name='soft_deleted_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tradegroup',
            name='soft_delete_reason',
            field=models.CharField(blank=True, default='', max_length=128),
        ),
    ]
