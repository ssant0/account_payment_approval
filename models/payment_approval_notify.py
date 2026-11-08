# Copyright (C) 2026 ssant0
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html_escape

from .payment_approval import build_whatsapp_url, record_url


class PaymentApprovalNotify(models.TransientModel):
    _name = "payment.approval.notify"
    _description = "Notificación de aprobación de pago"

    invoice_ids = fields.Many2many("account.move", string="Facturas")
    approver_id = fields.Many2one("res.users", string="Aprobador", readonly=True)
    amount = fields.Monetary(
        string="Monto", currency_field="currency_id", readonly=True
    )
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    email_sent = fields.Boolean(string="Correo enviado", readonly=True)
    message = fields.Html(
        string="Mensaje", compute="_compute_message", sanitize=False
    )
    whatsapp_url = fields.Char(string="WhatsApp", compute="_compute_whatsapp")
    has_phone = fields.Boolean(compute="_compute_whatsapp")

    @api.depends(
        "invoice_ids", "approver_id", "amount", "currency_id", "email_sent",
        "has_phone",
    )
    def _compute_message(self):
        for rec in self:
            links = "".join(
                '<li><a href="%s">%s</a></li>'
                % (html_escape(record_url(inv)), html_escape(inv.name or inv.display_name))
                for inv in rec.invoice_ids
            )
            currency = rec.currency_id.name or ""
            if rec.email_sent:
                email_note = (
                    "<p>Se envió un correo al aprobador con el link a la "
                    "factura.</p>"
                )
            else:
                email_note = (
                    "<p>No se pudo enviar el correo (revisa el servidor SMTP). "
                    "Puedes notificarle por WhatsApp.</p>"
                )
            if not rec.has_phone:
                email_note += (
                    "<p>El aprobador no tiene un número de WhatsApp "
                    "configurado.</p>"
                )
            rec.message = (
                "<p>El pago de <b>%.2f %s</b> requiere la autorización de "
                "<b>%s</b>.</p>%s"
                "<p>Facturas:</p><ul>%s</ul>"
            ) % (
                rec.amount,
                html_escape(currency),
                html_escape(rec.approver_id.name or ""),
                email_note,
                links,
            )

    @api.depends("invoice_ids", "approver_id", "amount", "currency_id")
    def _compute_whatsapp(self):
        for rec in self:
            url = False
            if rec.approver_id and rec.currency_id:
                url = build_whatsapp_url(
                    rec.env, rec.approver_id, rec.invoice_ids, rec.amount, rec.currency_id
                )
            rec.whatsapp_url = url or False
            rec.has_phone = bool(url)

    def action_open_whatsapp(self):
        self.ensure_one()
        if not self.whatsapp_url:
            raise UserError(_(
                "El aprobador no tiene un número de WhatsApp configurado. "
                "Agrégalo en Contabilidad → Ajustes → Aprobación de pagos."
            ))
        return {
            "type": "ir.actions.act_url",
            "url": self.whatsapp_url,
            "target": "new",
        }
