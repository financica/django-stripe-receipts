from django.core.management.base import BaseCommand
from djstripe import models

from financica.lib.stripe import creation


class Command(BaseCommand):
    help = "Create Financica transactions from Stripe API data"

    def handle(self, *args, **options):
        invoices = models.Invoice.objects.all()
        for invoice in invoices:
            creation.create_legs_from_invoice(invoice)
            creation.add_vat_collected_to_transaction(invoice)
