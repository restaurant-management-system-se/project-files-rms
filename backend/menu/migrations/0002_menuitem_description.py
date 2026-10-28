from django.db import migrations, models
class Migration(migrations.Migration):
    dependencies = [('menu', '0001_initial')]
    operations = [migrations.AddField(model_name='menuitem', name='description', field=models.TextField(blank=True, max_length=2000))]
