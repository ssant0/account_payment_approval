# AGENTS.md — Aprobación de Registro de Pagos

Módulo Odoo 19 Community. El nombre técnico es `account_payment_approval` y
**debe coincidir con el nombre de la carpeta**: Odoo lo usa para instalar,
actualizar y registrar los XML IDs.

## Contexto del repo

- Addon standalone: no hay tests, linter, CI ni runtime de Odoo en este repo.
- Manifiesto: `19.0.1.0.0`, depende de `account` y `mail`.
- Código, UI, comentarios y docs en español. Mantén los mensajes de usuario
  envueltos en `_()`.
- Para probarlo, coloca esta carpeta en el `addons_path` de una instancia
  Odoo 19 e instala/actualiza con
  `odoo -d <db> -i account_payment_approval --stop-after-init` o `-u`.

## Mapa de la lógica

- `models/payment_approval.py`: única fuente de la regla y las notificaciones
  (`get_approval_requirement`, `check_payment_approval`, correo y URL wa.me).
  No dupliques validaciones en otros modelos.
- `models/account_payment_register.py`: intercepta el asistente **Registrar
  pago**. `action_create_payments` abre el diálogo sin crear el pago;
  `_init_payments` valida otra vez antes del asiento contable.
- `models/account_payment.py`: bloquea la confirmación manual (`action_post`)
  desde el menú Pagos.
- `models/payment_approval_notify.py`: `TransientModel` del diálogo; no
  persiste estados ni pagos pendientes.
- `models/res_config_settings.py` + `views/res_config_settings_views.xml`:
  ajustes en Contabilidad → Ajustes → Aprobación de pagos.
- `security/ir.model.access.csv`: acceso al modelo del diálogo.

## Reglas de negocio que no se deben romper

- La aprobación es "quien registra, autoriza". No hay flujo de solicitud ni
  estado pendiente; el pago se rechaza antes de crear el asiento.
- El aprobador configurado nunca se bloquea, y `env.su` (cron, uid 1) se
  permite por diseño.
- Se bloquea cuando el monto convertido a la moneda de la compañía es
  **igual o mayor** al mínimo (`compare_amounts(...) >= 0`).
- Si la opción está activa y no hay aprobador, se lanza `UserError`.
- Un fallo de SMTP no debe interrumpir el flujo: se registra y el diálogo
  ofrece WhatsApp como respaldo.
- Las URLs de registros usan el formato de Odoo 19:
  `{base_url}/odoo/{model}/{id}`.
- Los ajustes se guardan en `ir.config_parameter` con el prefijo
  `account_payment_approval.` (definido también en `res_config_settings.py`).

## Verificación manual

No hay suite automatizada. Con el módulo instalado, probar:

1. Como usuario distinto del aprobador, registrar un pago >= al mínimo: debe
   aparecer el diálogo y **no** crearse el pago.
2. Como aprobador, el mismo pago debe registrarse normal.
3. Un pago por debajo del mínimo debe pasar sin diálogo.
4. Confirmar un pago manual desde el menú Pagos con usuario no aprobador:
   debe rechazarse.

Si agregas tests, ejecuta solo este addon con
`--test-tags /account_payment_approval`.

## Trampas

- Cambiar el nombre de la carpeta cambia el nombre técnico del módulo. En una
  base donde ya estaba instalado con el nombre anterior, los registros de
  `ir.module.module`, los XML IDs y los parámetros antiguos no se renombran
  solos: hay que migrar o desinstalar/reinstalar.
- Los `config_parameter` son claves persistentes; renombrarlas deja la
  configuración anterior huérfana.
- El modelo se llama `payment.approval.notify` a propósito; no depende del
  nombre técnico del módulo.
- No hay carpeta `i18n/`; las cadenas visibles ya están en español.
