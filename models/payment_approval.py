# -*- coding: utf-8 -*-
# Copyright (C) 2026 ssant0
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html).
"""Regla de bloqueo de pagos y notificaciones al aprobador.

La aprobación es simple por diseño: si el pago alcanza el monto configurado,
solo el usuario aprobador puede registrarlo. No se crean estados intermedios
ni pagos a medias; el asistente lanza un diálogo antes de crear el asiento.
"""

import logging
import re
from urllib.parse import quote

from odoo import _, fields
from odoo.exceptions import UserError
from odoo.tools import html_escape, str2bool

_logger = logging.getLogger(__name__)

PARAM_ENABLED = "account_payment_approval.enabled"
PARAM_AMOUNT = "account_payment_approval.amount"
PARAM_USER = "account_payment_approval.user_id"
PARAM_WHATSAPP = "account_payment_approval.whatsapp"


def _to_date(value):
    if not value:
        return fields.Date.today()
    if isinstance(value, str):
        return fields.Date.to_date(value)
    return value


def record_url(record):
    """URL estable de Odoo 19 para abrir un registro."""
    return f"{record.get_base_url()}/odoo/{record._name}/{record.id}"


def get_whatsapp_phone(env, approver):
    """Número del aprobador: ajuste explícito o teléfono/móvil del contacto."""
    params = env["ir.config_parameter"].sudo()
    phone = (
        params.get_param(PARAM_WHATSAPP)
        or approver.partner_id.mobile
        or approver.partner_id.phone
        or ""
    )
    digits = re.sub(r"\D", "", phone)
    return digits or False


def get_approval_requirement(env, amount, currency=None, company=None, date=None):
    """Devuelve (requiere_aprobacion, aprobador)."""
    empty_user = env["res.users"]
    # Operaciones del sistema (cron, uid 1) no se bloquean.
    if env.su:
        return False, empty_user

    params = env["ir.config_parameter"].sudo()
    if not str2bool(params.get_param(PARAM_ENABLED, default=False)):
        return False, empty_user

    company = company or env.company
    currency = currency or company.currency_id
    date = _to_date(date)

    approver_id = params.get_param(PARAM_USER)
    try:
        approver_id = int(approver_id)
    except (TypeError, ValueError):
        approver_id = 0

    if not approver_id:
        raise UserError(_(
            "No hay un aprobador de pagos configurado. Ve a Contabilidad → "
            "Ajustes → Aprobación de pagos y elige quién autoriza los pagos."
        ))

    approver = env["res.users"].browse(approver_id)
    if env.user.id == approver_id:
        return False, approver

    threshold = float(params.get_param(PARAM_AMOUNT, default=1.0))
    amount_company = currency._convert(amount, company.currency_id, company, date)
    if company.currency_id.compare_amounts(amount_company, threshold) >= 0:
        return True, approver
    return False, approver


def check_payment_approval(env, amount, currency=None, company=None, date=None):
    """Lanza UserError si el pago requiere aprobación y el usuario no lo es."""
    required, approver = get_approval_requirement(
        env, amount, currency=currency, company=company, date=date
    )
    if required:
        raise UserError(_(
            "El pago de %.2f %s requiere autorización de %s. "
            "Pídele que registre el pago."
        ) % (amount, (currency or company.currency_id).name, approver.name))


def invoices_html(invoices):
    items = "".join(
        '<li><a href="%s">%s</a></li>'
        % (html_escape(record_url(inv)), html_escape(inv.name or inv.display_name))
        for inv in invoices
    )
    return f"<ul>{items}</ul>"


def notify_approver_by_email(env, invoices, approver, amount, currency):
    """Envía al aprobador un correo con el link directo a la factura."""
    email_to = approver.partner_id.email
    if not email_to:
        _logger.warning(
            "El aprobador %s no tiene correo; no se envió la notificación.",
            approver.name,
        )
        return False

    names = ", ".join(invoices.mapped("name")) or _("pago")
    body = (
        "<p>Se intentó registrar un pago de "
        f"<b>{amount:.2f} {html_escape(currency.name)}</b> que requiere tu "
        "autorización.</p>"
        f"<p>Facturas:</p>{invoices_html(invoices)}"
        "<p>Entra a Odoo con tu usuario y registra el pago desde la factura.</p>"
    )
    email_from = (
        env.company.partner_id.email_formatted
        or env.user.partner_id.email_formatted
        or False
    )
    mail_values = {
        "subject": _("Pago pendiente de aprobación: %s") % names,
        "body_html": body,
        "email_to": email_to,
        "email_from": email_from,
    }
    if len(invoices) == 1:
        mail_values.update({"model": "account.move", "res_id": invoices.id})
    mail = env["mail.mail"].sudo().create(mail_values)
    try:
        mail.send()
        return True
    except Exception:  # noqa: BLE001 - no bloquear el flujo si falla el SMTP
        _logger.exception(
            "No se pudo enviar el correo de aprobación para las facturas %s",
            invoices.ids,
        )
        return False


def build_whatsapp_url(env, approver, invoices, amount, currency):
    """Link wa.me con el número del aprobador y las facturas."""
    phone = get_whatsapp_phone(env, approver)
    if not phone:
        return False
    links = " ".join(
        f"{inv.name or inv.display_name}: {record_url(inv)}" for inv in invoices
    )
    text = (
        f"Hola {approver.name}, el pago de {amount:.2f} {currency.name} "
        f"requiere tu aprobación. {links}"
    )
    return f"https://wa.me/{phone}?text={quote(text)}"
