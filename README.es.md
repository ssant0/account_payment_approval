# 💳 Aprobación de Registro de Pagos

[English](./README.md) | **Español**

[![Odoo](https://img.shields.io/badge/Odoo-19.0%20Community-875A7B?logo=odoo&logoColor=white)](https://www.odoo.com/)
[![Versión](https://img.shields.io/badge/versi%C3%B3n-19.0.1.0.0-blue)](./__manifest__.py)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Licencia](https://img.shields.io/badge/licencia-LGPL--3-green)](./LICENSE)

Addon de Odoo 19 que exige que un **aprobador designado** registre los pagos
que alcanzan o superan un monto configurable. Si otro usuario lo intenta, el
pago no se crea: se notifica al aprobador por correo y por WhatsApp.

## Descripción

En muchas empresas el registro de pagos debe pasar por una persona de
confianza. Este módulo intercepta el asistente **Registrar pago** y la
confirmación manual desde el menú **Pagos**, y bloquea la operación antes de
crear el asiento contable cuando el monto supera el límite. La autorización es
simple por diseño: **quien registra el pago es quien lo autoriza**. No hay
estados pendientes, solicitudes en cola ni pagos a medias.

## Tabla de contenidos

- [Descripción](#descripción)
- [Cómo funciona](#cómo-funciona)
- [Stack tecnológico](#stack-tecnológico)
- [Requisitos previos](#requisitos-previos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Comandos disponibles](#comandos-disponibles)
- [Estructura del módulo](#estructura-del-módulo)
- [Verificación manual](#verificación-manual)
- [Solución de problemas](#solución-de-problemas)
- [Limitaciones](#limitaciones)
- [Contribuir](#contribuir)
- [Licencia](#licencia)

## Cómo funciona

1. Un usuario abre el asistente **Registrar pago** sobre una o varias facturas
   y pulsa **Crear pagos**.
2. `account.payment.register.action_create_payments` evalúa la regla con
   `get_approval_requirement`. Si el monto convertido a la moneda de la
   compañía es **igual o mayor** al mínimo, el pago **no se crea**.
3. Se envía un correo al aprobador con el link directo a cada factura y se
   abre el diálogo **Pago pendiente de aprobación** con el detalle, el estado
   del correo y un botón **Notificar por WhatsApp**.
4. El aprobador entra a Odoo con su usuario y registra el pago desde la
   factura. Ese registro constituye la autorización.
5. Como red de seguridad, `_init_payments` revalida justo antes de crear el
   asiento contable, y `account.payment.action_post` bloquea la confirmación
   manual desde el menú **Pagos**.

No se bloquean:

- Al **aprobador** configurado.
- Las operaciones de sistema (`env.su`: cron, uid 1).
- Los pagos por debajo del monto mínimo.
- Las instalaciones con la opción desactivada.

> [!NOTE]
> El monto se compara en la moneda de la compañía. Si el pago es en otra
> moneda, se convierte con el tipo de cambio de la fecha del pago.

> [!IMPORTANT]
> Un fallo del servidor SMTP no interrumpe el bloqueo: se registra en el log,
> el diálogo avisa que el correo no se envió y el botón de WhatsApp sigue
> disponible como respaldo.

> [!WARNING]
> Los links de los correos y del diálogo usan `web.base.url`. Debe apuntar al
> dominio público de la instancia; si queda en `localhost`, los enlaces no
> servirán para el aprobador.

## Stack tecnológico

- **Odoo 19 Community** (addon de `account` y `mail`).
- **Python 3.10+**.
- **PostgreSQL** como base de datos de la instancia.
- **XML/QWeb** para vistas y ajustes.
- **CSV** para reglas de acceso.
- Sin dependencias externas de Python.

## Requisitos previos

- Una instancia funcional de **Odoo 19 Community**.
- **Python 3.10 o superior**, según lo requiera tu instalación de Odoo.
- **PostgreSQL** accesible por la instancia.
- El módulo base **Contabilidad** (`account`) instalado.
- Acceso de administrador para instalar el addon y editar los ajustes.
- SMTP configurado si quieres que el correo al aprobador salga (opcional;
  WhatsApp funciona sin SMTP).

## Instalación

### 1. Copiar el addon al `addons_path`

```bash
# Opción A: copiar la carpeta del addon
cp -R account_payment_approval /opt/odoo/custom-addons/
```

```bash
# Opción B: clonar el repositorio, si está versionado en Git
git clone <url-del-repositorio> /opt/odoo/custom-addons/account_payment_approval
```

> [!IMPORTANT]
> La carpeta debe llamarse exactamente `account_payment_approval`. Odoo usa el
> nombre de la carpeta como nombre técnico del módulo para instalarlo,
> actualizarlo y registrar sus XML IDs.

### 2. Registrar el directorio en la configuración

Añade la carpeta a `addons_path` en tu `odoo.conf`:

```ini
[options]
addons_path = /opt/odoo/custom-addons,/opt/odoo/addons
```

### 3. Reiniciar la instancia

```bash
sudo systemctl restart odoo
```

### 4. Instalar el módulo

Desde la interfaz: **Aplicaciones → Actualizar lista de aplicaciones**, busca
**Aprobación de Registro de Pagos** e instala.

O por línea de comandos:

```bash
odoo -d mi_base -i account_payment_approval --stop-after-init
```

Si tu instalación usa el binario `odoo-bin`, sustituye `odoo` por `odoo-bin`.

Para aplicar cambios después de actualizar el código:

```bash
odoo -d mi_base -u account_payment_approval --stop-after-init
```

## Configuración

Ve a **Contabilidad → Ajustes → Aprobación de pagos**. El bloque solo es
visible para usuarios con permisos de administración de contabilidad.

| Ajuste | Parámetro (`ir.config_parameter`) | Valor por defecto | Descripción |
|---|---|---|---|
| Requerir aprobación para pagos | `account_payment_approval.enabled` | `False` | Activa el bloqueo. |
| Monto mínimo | `account_payment_approval.amount` | `1.0` | En moneda de la compañía. Se bloquea si el monto convertido es igual o mayor. |
| Aprobador | `account_payment_approval.user_id` | vacío | Usuario interno (`share = False`) que puede registrar los pagos bloqueados. |
| WhatsApp del aprobador | `account_payment_approval.whatsapp` | vacío | Número con código de país, solo dígitos (ej. `5216681234567`). Si se deja vacío, se usa el móvil o teléfono del contacto del aprobador. |

> [!IMPORTANT]
> Si la opción está activa y no hay aprobador configurado, cualquier pago
> lanza un `UserError` que pide configurarlo. No se permite operar a ciegas.

> [!NOTE]
> El aprobador necesita permisos de **Facturación/Contabilidad** para poder
> registrar el pago. Si no los tiene, Odoo no le mostrará la acción.

### Variables de entorno

Este addon **no lee variables de entorno**. Toda su configuración vive en
`ir.config_parameter` con el prefijo `account_payment_approval.` y se edita
desde los ajustes de Contabilidad.

## Uso

1. Activa **Requerir aprobación para pagos** y elige un aprobador.
2. Define el **monto mínimo** en la moneda de la compañía.
3. Como usuario distinto del aprobador, registra un pago igual o mayor al
   mínimo: aparecerá el diálogo y **no** se creará el pago.
4. El aprobador recibe el correo (si hay SMTP) y puede registrarlo él mismo.
5. Si el correo falla o no hay SMTP, usa **Notificar por WhatsApp** desde el
   diálogo para abrir `wa.me` con el número y el link de la factura
   prellenados.

Para que los vendedores no vean el botón de registro de pagos, quítales el
grupo **Facturación** (`account.group_account_invoice`). Aunque lo conserven,
el módulo rechaza el intento con un mensaje que indica quién debe autorizarlo.

## Comandos disponibles

El repositorio no incluye `Makefile`, `package.json` ni un runner de tareas.
Los comandos relevantes son los de Odoo:

| Comando | Propósito |
|---|---|
| `odoo -d <db> -i account_payment_approval --stop-after-init` | Instalar el módulo. |
| `odoo -d <db> -u account_payment_approval --stop-after-init` | Actualizar el módulo tras cambios en código, vistas o seguridad. |
| `odoo -d <db> -u account_payment_approval --test-tags /account_payment_approval --stop-after-init` | Ejecutar la suite del addon cuando exista. Hoy no hay tests automatizados. |
| `odoo shell -d <db>` | Consola interactiva para inspeccionar parámetros o usuarios. |

## Estructura del módulo

```text
account_payment_approval/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── payment_approval.py              # Regla única, correo y URL wa.me
│   ├── account_payment_register.py      # Asistente "Registrar pago"
│   ├── account_payment.py               # Confirmación manual desde Pagos
│   ├── payment_approval_notify.py       # Diálogo transitorio
│   └── res_config_settings.py           # Ajustes de Contabilidad
├── security/
│   └── ir.model.access.csv
├── views/
│   ├── payment_approval_notify_views.xml
│   └── res_config_settings_views.xml
├── AGENTS.md
├── LICENSE
├── README.md
└── README.es.md
```

`models/payment_approval.py` es la **única fuente de la regla y las
notificaciones**. Si otro módulo necesita reutilizarla, debe llamar a
`get_approval_requirement` o `check_payment_approval` en lugar de duplicar la
validación.

## Verificación manual

No hay suite automatizada ni CI en este repositorio. Con el módulo instalado,
comprueba:

1. Como usuario distinto del aprobador, registra un pago igual o mayor al
   mínimo: debe aparecer el diálogo y **no** crearse el pago.
2. Como aprobador, el mismo pago debe registrarse con normalidad.
3. Un pago por debajo del mínimo debe pasar sin diálogo.
4. Confirma un pago manual desde el menú **Pagos** con un usuario no aprobador:
   debe rechazarse.
5. Desactiva la opción y verifica que todos los usuarios pueden registrar
   pagos.
6. Prueba un pago en otra moneda y confirma que la comparación usa el tipo de
   cambio de la fecha del pago.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| El módulo no aparece en Aplicaciones | La carpeta no está en `addons_path` o falta reiniciar | Revisa `odoo.conf`, reinicia y actualiza la lista de aplicaciones. |
| Error al instalar por nombre de módulo | La carpeta no se llama `account_payment_approval` | Renombra la carpeta y vuelve a intentar. |
| El aprobador no recibe el correo | SMTP no configurado o correo del contacto vacío | Configura el servidor de correo y el email del aprobador; usa WhatsApp como respaldo. |
| Los links abren `localhost` | `web.base.url` no apunta al dominio público | Ajusta `web.base.url` en Parámetros del sistema. |
| No aparece el botón de WhatsApp | El aprobador no tiene número configurado | Define **WhatsApp del aprobador** o el teléfono/móvil de su contacto. |
| El aprobador no puede registrar el pago | Le faltan permisos de Facturación/Contabilidad | Asígnale el grupo correspondiente. |
| Cambié el nombre de la carpeta y el módulo falla | El nombre técnico cambió y los registros antiguos no se renombran | Migra los XML IDs y parámetros, o desinstala y reinstala. |

## Limitaciones

- La aprobación es **"quien registra, autoriza"**: no existe un flujo de
  "envío la solicitud y otro la aprueba después". Eso requeriría un módulo con
  pagos en estado pendiente y conciliación diferida.
- No se persiste ningún estado de aprobación: el diálogo es transitorio.
- La comparación siempre se hace en la moneda de la compañía.
- El envío de correo depende del SMTP de Odoo; el módulo no lo configura.
- No hay integración con la API de WhatsApp: solo se genera un enlace `wa.me`.

## Contribuir

- Escribe código, comentarios, mensajes de usuario y documentación **en
  español**.
- Envuelve los mensajes visibles con `_()` de Odoo.
- Mantén la regla de negocio en `models/payment_approval.py`; no dupliques
  validaciones en otros modelos.
- Si cambias vistas, seguridad o la lógica, sube la versión en
  `__manifest__.py` y actualiza el módulo con `-u`.
- Ejecuta la [verificación manual](#verificación-manual) antes de dar un cambio
  por terminado. No hay linter, CI ni suite de tests en el repositorio.
- No renombres la carpeta ni las claves `account_payment_approval.*`: son
  identificadores persistentes en la base de datos.

## Licencia

Este addon es **software libre y gratuito** para todos. Se distribuye bajo la
**GNU Lesser General Public License v3.0** (LGPL-3), la misma licencia que
Odoo. Puedes usarlo, modificarlo y redistribuirlo conforme a sus términos.

El texto completo de la licencia está en [`LICENSE`](./LICENSE), que incluye
la LGPL-3 y el texto de la GPL-3 al que aquella remite.

Autor: **ssant0**.
