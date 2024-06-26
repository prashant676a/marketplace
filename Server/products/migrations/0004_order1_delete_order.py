# Generated by Django 4.1.6 on 2023-03-07 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0003_order_alter_product_store"),
    ]

    operations = [
        migrations.CreateModel(
            name="Order1",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order_message", models.CharField(max_length=255)),
                ("ordered_by", models.CharField(default="", max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.DeleteModel(
            name="Order",
        ),
    ]
