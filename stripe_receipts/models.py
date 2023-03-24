from django.db import models

from .utils import STRIPE_DASH, STRIPE_PAY


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

    # receipt_html = FileAttachmentField(
    #     upload_to="stripe/receipts/",
    #     related_name="stripe_html_receipts",
    #     help_text="The receipt, as HTML",
    # )
    # receipt_pdf = FileAttachmentField(
    #     upload_to="stripe/receipts/",
    #     related_name="stripe_pdf_receipts",
    #     help_text="The receipt, as PDF (sometimes unavailable)",
    # )

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def permalink(self):
        if self.type == "rcpt":
            return f"{STRIPE_PAY}/receipts/{self.account_id}/{self.charge_id}/{self.id}"
        return f"{STRIPE_DASH}/emails/receipts/{self.id}"

    def __str__(self):
        return f"#{self.receipt_number} ({self.id})"
