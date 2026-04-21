from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('trades', '0003_rebuild_trade_groups_lifecycle'),
    ]

    operations = [
        migrations.CreateModel(
            name='TradeMatchedLot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('symbol', models.CharField(max_length=64)),
                ('side', models.CharField(blank=True, max_length=8, null=True)),
                ('matched_qty', models.DecimalField(decimal_places=6, max_digits=20)),
                ('open_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('close_price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('realized_pnl', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('commission_total', models.DecimalField(decimal_places=8, default=0, max_digits=20)),
                ('opened_at', models.DateTimeField(blank=True, null=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('trade_group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='matched_lots', to='trades.tradegroup')),
            ],
        ),
    ]
