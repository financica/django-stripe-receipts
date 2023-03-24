from io import BytesIO

import requests
from django.core.management.base import BaseCommand

from financica.apps.stripe_receipts.models import Receipt
from financica.utils import get_content_disposition_filename


class Command(BaseCommand):
    help = "Load data for one or more Square invoice (by invoice ID)"

    def add_arguments(self, parser):
        parser.add_argument("receipt_id", nargs="+")

    def handle(self, *args, **options):
        for receipt_id in options["receipt_id"]:
            if Receipt.objects.filter(id=receipt_id).exists():
                self.stdout.write("Receipt {receipt_id} already exists, skipping…")
                continue

            receipt_url, receipt_pdf_url = Receipt.urls_for_id(receipt_id)

            resp = requests.get(receipt_url)
            try:
                resp.raise_for_status()

            except requests.HTTPError as err:
                self.stderr.write(f"Error getting receipt {receipt_id}: {err}")

            else:
                receipt, _created = Receipt.objects.get_or_create(
                    id=receipt_id,
                    defaults={
                        "type": receipt_id.rpartition("_")[0],
                        **Receipt.parse_html_receipt(resp.content),
                    },
                )

                # Save the HTML receipt
                receipt.set_receipt_html(
                    BytesIO(resp.content),
                    filename=f"{receipt_id}.html",
                    source_url=resp.request.url,
                    metadata={"type": "RECEIPT_EMAIL"},
                )

                # Download receipt as PDF
                # (Expect a redirect, so allow_redirects=False)
                resp = requests.get(receipt_pdf_url, allow_redirects=False)
                if resp.status_code == 302:
                    redir_url = resp.headers.get("location")
                    resp = requests.get(redir_url, stream=True)
                    receipt.set_receipt_pdf(
                        resp.raw,
                        filename=get_content_disposition_filename(
                            resp.headers["content-disposition"]
                        ),
                        source_url=redir_url,
                        metadata={
                            "type": "RECEIPT",
                            "stripe_original_url": receipt_pdf_url,
                            "stripe_file_id": Receipt.parse_file_id(redir_url),
                        },
                    )
                else:
                    self.stderr.write(
                        f"PDF not available (status code {resp.status_code})"
                    )
