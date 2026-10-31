import uuid
from django.db import migrations,models
import django.db.models.deletion
class Migration(migrations.Migration):
    dependencies=[('orders','0003_order_version')]
    operations=[migrations.CreateModel(name='OrderEvent',fields=[('id',models.UUIDField(default=uuid.uuid4,editable=False,primary_key=True,serialize=False)),('version',models.PositiveIntegerField()),('status',models.CharField(max_length=10)),('timestamp',models.DateTimeField(auto_now_add=True)),('delivered_at',models.DateTimeField(null=True,blank=True)),('order',models.ForeignKey(on_delete=django.db.models.deletion.PROTECT,to='orders.order'))],options={'constraints':[models.UniqueConstraint(fields=('order','version'),name='order_event_version_unique')]})]
