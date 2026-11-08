# Copyright (C) 2026 ssant0
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    payment_approval_enabled = fields.Boolean(
        string="Requerir aprobación para pagos",
        config_parameter="account_payment_approval.enabled",
        help="Si se activa, los pagos iguales o mayores al monto mínimo solo "
             "pueden registrarse por el aprobador seleccionado.",
    )
    payment_approval_amount = fields.Float(
        string="Monto mínimo",
        default=1.0,
        config_parameter="account_payment_approval.amount",
        help="Monto en la moneda de la compañía. Los pagos iguales o "
             "mayores a este monto requieren al aprobador.",
    )
    payment_approval_user_id = fields.Many2one(
        "res.users",
        string="Aprobador",
        config_parameter="account_payment_approval.user_id",
        domain=[("share", "=", False)],
        help="Solo este usuario puede registrar pagos iguales o mayores al "
             "monto mínimo. Debe tener permisos de Facturación/Contabilidad "
             "para poder registrar pagos.",
    )
    payment_approval_whatsapp = fields.Char(
        string="WhatsApp del aprobador",
        config_parameter="account_payment_approval.whatsapp",
        help="Número con código de país, sin + ni espacios "
             "(ej. 5216681234567). Si se deja vacío, se usa el teléfono "
             "del aprobador.",
    )
