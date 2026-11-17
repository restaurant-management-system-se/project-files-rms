from django.conf import settings
from django.db import migrations,models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[('orders','0001_initial'),migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations=[migrations.CreateModel(name='OrderRequestKey',fields=[('id',models.BigAutoField(auto_created=True,primary_key=True,serialize=False,verbose_name='ID')),('key',models.UUIDField()),('payload',models.JSONField()),('customer',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to=settings.AUTH_USER_MODEL)),('order',models.OneToOneField(on_delete=django.db.models.deletion.PROTECT,to='orders.order'))],options={'constraints':[models.UniqueConstraint(fields=('customer','key'),name='order_customer_retry_unique')]})]
