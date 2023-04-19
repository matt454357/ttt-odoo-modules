# Copyright 2020 Matt Taylor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Invoice Calendar Events",
    "summary": "Link events to invoice lines.",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "author": "Matt Taylor",
    "website": "https://github.com/matt454357/ttt-odoo-modules",
    "category": "Invoices & Payments",
    "depends": ["account", "calendar"],
    "license": "AGPL-3",
    "data": [
        "views/calendar_event_views.xml",
        "views/account_invoice_views.xml",
    ],
    'installable': True,
}
