from django.db import migrations,models
class Migration(migrations.Migration):
    dependencies=[('orders','0002_orderrequestkey')]
    operations=[migrations.AddField(model_name='order',name='version',field=models.PositiveIntegerField(default=1))]
