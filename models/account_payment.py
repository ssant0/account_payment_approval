# Copyright (C) 2026 ssant0
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import models

from .payment_approval import check_payment_approval


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def action_post(self):
        """Cubre la confirmación manual de pagos desde el menú Pagos."""
        for payment in self:
            check_payment_approval(
                self.env,
                payment.amount,
                currency=payment.currency_id,
                company=payment.company_id,
                date=payment.date,
            )
        return super().action_post()
