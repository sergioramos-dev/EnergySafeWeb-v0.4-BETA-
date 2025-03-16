
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import main.models

class Migration(migrations.Migration):

    dependencies = [
        ('main', '0002_auto_20250224_0852'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserSession',
            fields=[
                ('id', models.CharField(default=main.models.CustomUser.generate_id, editable=False, max_length=24, primary_key=True, serialize=False)),
                ('session_key', models.CharField(max_length=40, unique=True)),
                ('session_data', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('last_activity', models.DateTimeField(default=django.utils.timezone.now)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='main.customuser')),
            ],
            options={
                'db_table': 'user_sessions',
            },
        ),
    ]