# 💳 Payment Registration Approval

**English** | [Español](./README.es.md)

[![Odoo](https://img.shields.io/badge/Odoo-19.0%20Community-875A7B?logo=odoo&logoColor=white)](https://www.odoo.com/)
[![Version](https://img.shields.io/badge/version-19.0.1.0.0-blue)](./__manifest__.py)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-LGPL--3-green)](./LICENSE)

Odoo 19 addon that requires a **designated approver** to register payments
that reach or exceed a configurable amount. If any other user tries, the
payment is not created: the approver is notified by email and WhatsApp.

## Description

In many companies, registering payments must go through a trusted person.
This module intercepts the **Register payment** wizard and the manual
confirmation from the **Payments** menu, and blocks the operation before the
journal entry is created when the amount exceeds the limit. Authorization is
simple by design: **whoever registers the payment is the one who authorizes
it**. There are no pending states, queued requests, or half-created payments.

## Table of contents

- [Description](#description)
- [How it works](#how-it-works)
- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Available commands](#available-commands)
- [Module structure](#module-structure)
- [Manual verification](#manual-verification)
- [Troubleshooting](#troubleshooting)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [License](#license)

## How it works

1. A user opens the **Register payment** wizard on one or more invoices and
   clicks **Create payments**.
2. `account.payment.register.action_create_payments` evaluates the rule with
   `get_approval_requirement`. If the amount converted to the company currency
   is **equal to or greater than** the minimum, the payment **is not created**.
3. An email is sent to the approver with a direct link to each invoice, and
   the **Payment pending approval** dialog opens with the details, the email
   status, and a **Notify by WhatsApp** button.
4. The approver logs into Odoo with their own user and registers the payment
   from the invoice. That registration constitutes the authorization.
5. As a safety net, `_init_payments` revalidates right before creating the
   journal entry, and `account.payment.action_post` blocks manual confirmation
   from the **Payments** menu.

The following are not blocked:

- The configured **approver**.
- System operations (`env.su`: cron, uid 1).
- Payments below the minimum amount.
- Installations where the option is disabled.

> [!NOTE]
> The amount is compared in the company currency. If the payment is in another
> currency, it is converted using the exchange rate of the payment date.

> [!IMPORTANT]
> An SMTP server failure does not interrupt the block: it is logged, the dialog
> warns that the email was not sent, and the WhatsApp button remains available
> as a fallback.

> [!WARNING]
> Email and dialog links use `web.base.url`. It must point to the instance's
> public domain; if it stays on `localhost`, the links will not work for the
> approver.

## Tech stack

- **Odoo 19 Community** (addon for `account` and `mail`).
- **Python 3.10+**.
- **PostgreSQL** as the instance database.
- **XML/QWeb** for views and settings.
- **CSV** for access rules.
- No external Python dependencies.

## Prerequisites

- A working **Odoo 19 Community** instance.
- **Python 3.10 or higher**, as required by your Odoo installation.
- **PostgreSQL** reachable by the instance.
- The base **Accounting** module (`account`) installed.
- Administrator access to install the addon and edit the settings.
- SMTP configured if you want the approver email to be sent (optional;
  WhatsApp works without SMTP).

## Installation

### 1. Copy the addon into `addons_path`

```bash
# Option A: copy the addon folder
cp -R account_payment_approval /opt/odoo/custom-addons/
```

```bash
# Option B: clone the repository, if it is versioned in Git
git clone <repository-url> /opt/odoo/custom-addons/account_payment_approval
```

> [!IMPORTANT]
> The folder must be named exactly `account_payment_approval`. Odoo uses the
> folder name as the module's technical name to install it, update it, and
> register its XML IDs.

### 2. Register the directory in the configuration

Add the folder to `addons_path` in your `odoo.conf`:

```ini
[options]
addons_path = /opt/odoo/custom-addons,/opt/odoo/addons
```

### 3. Restart the instance

```bash
sudo systemctl restart odoo
```

### 4. Install the module

From the UI: **Apps → Update Apps List**, search for **Aprobación de Registro
de Pagos** and install it.

Or from the command line:

```bash
odoo -d my_db -i account_payment_approval --stop-after-init
```

If your installation uses the `odoo-bin` binary, replace `odoo` with
`odoo-bin`.

To apply changes after updating the code:

```bash
odoo -d my_db -u account_payment_approval --stop-after-init
```

## Configuration

Go to **Accounting → Settings → Payment approval**. The block is only visible
to users with accounting administration permissions.

| Setting | Parameter (`ir.config_parameter`) | Default value | Description |
|---|---|---|---|
| Require approval for payments | `account_payment_approval.enabled` | `False` | Enables the block. |
| Minimum amount | `account_payment_approval.amount` | `1.0` | In company currency. Blocked when the converted amount is equal to or greater. |
| Approver | `account_payment_approval.user_id` | empty | Internal user (`share = False`) allowed to register blocked payments. |
| Approver WhatsApp | `account_payment_approval.whatsapp` | empty | Number with country code, digits only (e.g. `5216681234567`). If empty, the approver contact's mobile or phone is used. |

> [!IMPORTANT]
> If the option is enabled and no approver is configured, any payment raises a
> `UserError` asking for one. Operating blindly is not allowed.

> [!NOTE]
> The approver needs **Invoicing/Accounting** permissions to register the
> payment. Without them, Odoo will not show the action.

### Environment variables

This addon **does not read environment variables**. All its configuration
lives in `ir.config_parameter` with the `account_payment_approval.` prefix and
is edited from the Accounting settings.

## Usage

1. Enable **Require approval for payments** and choose an approver.
2. Set the **minimum amount** in the company currency.
3. As a user other than the approver, register a payment equal to or greater
   than the minimum: the dialog will appear and the payment will **not** be
   created.
4. The approver receives the email (if SMTP is configured) and can register it
   themselves.
5. If the email fails or there is no SMTP, use **Notify by WhatsApp** from the
   dialog to open `wa.me` with the number and the invoice link prefilled.

To keep salespeople from seeing the payment registration button, remove the
**Invoicing** group (`account.group_account_invoice`) from them. Even if they
keep it, the module rejects the attempt with a message indicating who must
authorize it.

## Available commands

The repository does not include a `Makefile`, `package.json`, or a task
runner. The relevant commands are Odoo's:

| Command | Purpose |
|---|---|
| `odoo -d <db> -i account_payment_approval --stop-after-init` | Install the module. |
| `odoo -d <db> -u account_payment_approval --stop-after-init` | Update the module after changes to code, views, or security. |
| `odoo -d <db> -u account_payment_approval --test-tags /account_payment_approval --stop-after-init` | Run the addon suite when it exists. There are no automated tests today. |
| `odoo shell -d <db>` | Interactive console to inspect parameters or users. |

## Module structure

```text
account_payment_approval/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── payment_approval.py              # Single rule, email and wa.me URL
│   ├── account_payment_register.py      # "Register payment" wizard
│   ├── account_payment.py               # Manual confirmation from Payments
│   ├── payment_approval_notify.py       # Transient dialog
│   └── res_config_settings.py           # Accounting settings
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

`models/payment_approval.py` is the **single source of the rule and the
notifications**. If another module needs to reuse it, it must call
`get_approval_requirement` or `check_payment_approval` instead of duplicating
the validation.

## Manual verification

There is no automated suite or CI in this repository. With the module
installed, check:

1. As a user other than the approver, register a payment equal to or greater
   than the minimum: the dialog must appear and the payment must **not** be
   created.
2. As the approver, the same payment must register normally.
3. A payment below the minimum must go through without a dialog.
4. Confirm a manual payment from the **Payments** menu with a non-approver
   user: it must be rejected.
5. Disable the option and verify that all users can register payments.
6. Test a payment in another currency and confirm that the comparison uses the
   exchange rate of the payment date.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| The module does not appear in Apps | The folder is not in `addons_path` or the instance was not restarted | Check `odoo.conf`, restart, and update the apps list. |
| Error installing by module name | The folder is not named `account_payment_approval` | Rename the folder and try again. |
| The approver does not receive the email | SMTP not configured or contact email empty | Configure the mail server and the approver's email; use WhatsApp as a fallback. |
| Links open `localhost` | `web.base.url` does not point to the public domain | Set `web.base.url` in System Parameters. |
| The WhatsApp button does not appear | The approver has no number configured | Set **Approver WhatsApp** or the phone/mobile of their contact. |
| The approver cannot register the payment | Missing Invoicing/Accounting permissions | Assign the corresponding group. |
| I renamed the folder and the module fails | The technical name changed and old records are not renamed | Migrate the XML IDs and parameters, or uninstall and reinstall. |

## Limitations

- Approval is **"whoever registers, authorizes"**: there is no "submit the
  request and someone approves it later" flow. That would require a module
  with payments in a pending state and deferred reconciliation.
- No approval state is persisted: the dialog is transient.
- The comparison is always made in the company currency.
- Email delivery depends on Odoo's SMTP; the module does not configure it.
- There is no WhatsApp API integration: only a `wa.me` link is generated.

## Contributing

- Write code, comments, user messages, and documentation **in Spanish**.
- Wrap visible messages with Odoo's `_()`.
- Keep the business rule in `models/payment_approval.py`; do not duplicate
  validations in other models.
- If you change views, security, or the logic, bump the version in
  `__manifest__.py` and update the module with `-u`.
- Run the [manual verification](#manual-verification) before considering a
  change done. There is no linter, CI, or test suite in the repository.
- Do not rename the folder or the `account_payment_approval.*` keys: they are
  persistent identifiers in the database.

## License

This addon is **free and open software** for everyone. It is distributed under
the **GNU Lesser General Public License v3.0** (LGPL-3), the same license as
Odoo. You may use, modify, and redistribute it under its terms.

The full license text is in [`LICENSE`](./LICENSE), which includes LGPL-3 and
the GPL-3 text it refers to.

Author: **ssant0**.
