# Copyright (C) 2026 ssant0
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models

from .payment_approval import (
    check_payment_approval,
    get_approval_requirement,
    notify_approver_by_email,
)


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def action_create_payments(self):
        """Si el pago requiere aprobación, notifica y abre el diálogo."""
        required, approver = get_approval_requirement(
            self.env,
            self.amount,
            currency=self.currency_id,
            company=self.company_id,
            date=self.payment_date,
        )
        if required:
            invoices = self.line_ids.move_id
            email_sent = notify_approver_by_email(
                self.env, invoices, approver, self.amount, self.currency_id
            )
            notify = self.env["payment.approval.notify"].create({
                "invoice_ids": [(6, 0, invoices.ids)],
                "approver_id": approver.id,
                "amount": self.amount,
                "currency_id": self.currency_id.id,
                "email_sent": email_sent,
            })
            return {
                "type": "ir.actions.act_window",
                "name": "Pago pendiente de aprobación",
                "res_model": "payment.approval.notify",
                "res_id": notify.id,
                "view_mode": "form",
                "target": "new",
            }
        return super().action_create_payments()

    def _init_payments(self, to_process, edit_mode=False):
        """Red de seguridad: valida antes de crear los asientos contables."""
        for item in to_process:
            vals = item.get("create_vals") or {}
            company = (
                self.env["res.company"].browse(vals["company_id"])
                if vals.get("company_id")
                else self.company_id
            )
            currency = (
                self.env["res.currency"].browse(vals["currency_id"])
                if vals.get("currency_id")
                else company.currency_id
            )
            check_payment_approval(
                self.env,
                vals.get("amount") or 0.0,
                currency=currency,
                company=company,
                date=vals.get("date") or fields.Date.today(),
            )
        return super()._init_payments(to_process, edit_mode=edit_mode)
