from django.db import migrations, models
import django.utils.timezone
from datetime import timedelta


def set_trial_dates(apps, schema_editor):
    Company = apps.get_model('core', 'Company')
    for company in Company.objects.all():
        if not company.trial_start_date:
            company.trial_start_date = company.created_at.date()
            company.trial_end_date = company.created_at.date() + timedelta(days=14)
            company.subscription_status = 'trial'
            company.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_add_user_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='company',
            name='trial_start_date',
            field=models.DateField(null=True, blank=True, verbose_name='بداية التجربة'),
        ),
        migrations.AddField(
            model_name='company',
            name='trial_end_date',
            field=models.DateField(null=True, blank=True, verbose_name='نهاية التجربة'),
        ),
        migrations.AddField(
            model_name='company',
            name='subscription_status',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('trial', 'تجريبي'),
                    ('active', 'مفعّل'),
                    ('expired', 'منتهي'),
                    ('suspended', 'موقوف'),
                ],
                default='trial',
                verbose_name='حالة الاشتراك',
            ),
        ),
        migrations.AddField(
            model_name='company',
            name='subscription_start_date',
            field=models.DateField(null=True, blank=True, verbose_name='بداية الاشتراك'),
        ),
        migrations.AddField(
            model_name='company',
            name='subscription_end_date',
            field=models.DateField(null=True, blank=True, verbose_name='نهاية الاشتراك'),
        ),
        migrations.AddField(
            model_name='company',
            name='subscription_notes',
            field=models.TextField(blank=True, null=True, verbose_name='ملاحظات الاشتراك'),
        ),
        migrations.RunPython(set_trial_dates, migrations.RunPython.noop),
    ]
