import re

import bs4
from django.db import models

from financica.lib.database.fields import FileAttachmentField

STRIPE_PAY = "https://pay.stripe.com"
STRIPE_DASH = "https://dashboard.stripe.com"


def _first_string_of_items(items, default=""):
    return (list(set(items)) + [""])[0]


class Receipt(models.Model):
    id = models.CharField(
        max_length=128,
        primary_key=True,
        editable=False,
        help_text="Stripe ID of the receipt (rcpt_*, invrc_* or pmtrc_*)",
    )
    type = models.CharField(
        max_length=16,
        choices=(
            ("rcpt", "Charge Receipt"),
            ("invrc", "Invoice Receipt"),
            ("pmtrc", "Payment Receipt"),
            ("rfdrc", "Refund Receipt"),
        ),
    )
    livemode = models.BooleanField(
        default=True, help_text="Whether the object is in live or test mode"
    )
    language = models.CharField(max_length=16, help_text="Language the receipt is in")
    receipt_number = models.CharField(
        max_length=128, db_index=True, help_text="End-user visible receipt number"
    )
    account_id = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text="Stripe ID of the account that owns the receipt (acct_*)",
    )
    customer_id = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text="Stripe ID of the customer issued the receipt (cus_*)",
    )
    invoice_id = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text="Stripe ID of the original invoice (in_*)",
    )
    invoice_number = models.CharField(
        max_length=128,
        blank=True,
        db_index=True,
        help_text="End-user visible invoice number",
    )

    receipt_html = FileAttachmentField(
        upload_to="stripe/receipts/",
        related_name="stripe_html_receipts",
        help_text="The receipt, as HTML",
    )
    receipt_pdf = FileAttachmentField(
        upload_to="stripe/receipts/",
        related_name="stripe_pdf_receipts",
        help_text="The receipt, as PDF (sometimes unavailable)",
    )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @staticmethod
    def urls_for_id(receipt_id: str):
        url = f"{STRIPE_DASH}/emails/receipts/{receipt_id}"
        return url, url + "/pdf"

    # TODO: move to financica.lib package
    @staticmethod
    def parse_html_receipt(data: bytes):
        soup = bs4.BeautifulSoup(data.decode(), "html.parser")
        html = soup.find("html")
        language = html.attrs["lang"]
        if language not in ("en", "fr"):
            raise NotImplementedError(
                f"Stripe Receipt parsing for language {language!r} not implemented"
            )
        _ = {
            "INVOICE_NUM": {
                "en": r"Invoice #([A-Z\d-]+)",
                "fr": r"Facture n°([A-Z\d-]+)",
            },
            "RECEIPT_NUM": {"en": r"#([\d-]+)", "fr": r"n°([\d-]+)"},
        }
        title = html.find("title").text
        testmode = title.startswith("TEST - ")
        table_text = " ".join(x.text for x in soup.find_all("table"))
        # add an empty string to default to an empty string if we haven't found any invoice number
        invoice_number = _first_string_of_items(
            re.findall(_["INVOICE_NUM"][language], table_text)
        )
        account_id = _first_string_of_items(
            re.findall(r"/(acct_[A-Za-z\d]+)/", str(soup))
        )

        return {
            "language": language,
            "livemode": not testmode,
            "receipt_number": re.findall(_["RECEIPT_NUM"][language], title)[-1],
            "account_id": account_id,
            "invoice_number": invoice_number,
        }

    # TODO: move to financica.lib package
    @staticmethod
    def parse_file_id(url: str) -> str:
        sre = re.match(r"https://files.stripe.com/files/(f_[A-Za-z0-9_]+)", url)
        if sre:
            return sre.group(1)
        return ""

    @property
    def permalink(self):
        if self.type == "rcpt":
            return f"{STRIPE_PAY}/receipts/{self.account_id}/{self.charge_id}/{self.id}"
        return f"{STRIPE_DASH}/emails/receipts/{self.id}"

    def __str__(self):
        return f"#{self.receipt_number} ({self.id})"
