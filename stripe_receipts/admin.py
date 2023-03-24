from django.contrib import admin

from . import models


@admin.register(models.Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    list_display = ("__str__", "type", "invoice_number", "livemode")
    list_filter = ("type", "livemode")
    raw_id_fields = ("receipt_html", "receipt_pdf")
    search_fields = ("id", "receipt_number", "invoice_number", "invoice_id")
