from django.db import migrations

def create_profiles(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('cms', 'UserProfile')
    Department = apps.get_model('cms', 'Department')
    
    # Create a default department if none exists
    if not Department.objects.exists():
        Department.objects.create(name="General", description="Default department")
    
    default_dept = Department.objects.first()
    
    for user in User.objects.all():
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'department': default_dept}
        )

class Migration(migrations.Migration):
    dependencies = [
        ('cms', '0002_alter_sharedfile_options_department_admin_and_more'),  # Replace with your actual last migration
    ]
    
    operations = [
        migrations.RunPython(create_profiles),
    ]
