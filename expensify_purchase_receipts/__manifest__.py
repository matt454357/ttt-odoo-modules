# Copyright 2024 Matt Taylor
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Expensify Purchase Receipts",
    "summary": "Import Expensify expense data as purchase receipts (out "
               "invoice) and create a bank statement.",
    "version": "15.0.1.0.0",
    "development_status": "Beta",
    "author": "Matt Taylor",
    "website": "https://github.com/matt454357/ttt-odoo-modules",
    'category': 'Accounting',
    "depends": ["account"],
    "license": "AGPL-3",
    "data": [
        "views/purchase_receipt_views.xml",
        "views/expensify_views.xml",
        "security/ir.model.access.csv",
    ],
    'installable': True,
}
