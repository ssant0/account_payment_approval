# Copyright (C) 2026 ssant0
# License LGPL-3.0 (https://www.gnu.org/licenses/lgpl-3.0.html).

{
    "name": "Aprobación de Registro de Pagos",
    "version": "19.0.1.0.0",
    "summary": "Bloquea el registro de pagos arriba de un monto configurable.",
    "description": """
Aprobación de Registro de Pagos
===============================

Bloquea el registro de pagos (facturas de cliente y proveedor) cuando el monto
alcanza o supera un límite configurable, salvo que el usuario que lo intenta
sea el aprobador designado en Ajustes.

- Monto mínimo configurable (por defecto 1.00 en la moneda de la compañía).
- Aprobador configurable (cualquier usuario interno).
- Al bloquear, envía un correo automático al aprobador con el link a la
  factura y abre un diálogo con un botón para notificarle por WhatsApp
  (wa.me) con el mismo link.
- Bloquea el asistente de "Registrar pago" antes de crear el asiento contable.
- También bloquea la confirmación manual de pagos desde el menú Pagos.
- El aprobador registra el pago él mismo (eso constituye la autorización).
""",
    "author": "ssant0",
    "license": "LGPL-3",
    "category": "Accounting/Payment",
    "depends": ["account", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_approval_notify_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
