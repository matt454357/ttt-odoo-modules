from odoo import models, fields, api


class ExpensifyLog(models.Model):
    _name = "expensify.log"
    _description = "Expensify import log"
    _order = "log_timestamp desc, name"

    name = fields.Char(
        string="Name",
        compute="_compute_name",
        store=True,
    )
    account_id = fields.Many2one(
        comodel_name='expensify.account',
        required=True,
    )
    log_timestamp = fields.Datetime(
        string="Log Time",
        required=True,
    )
    success = fields.Boolean(
        string="Success",
        required=True,
        default=False,
    )
    account_mail = fields.Char(
        string="Email",
        required=True,
    )
    expense_date = fields.Datetime(
        string="Exp Date",
        required=True,
    )
    merchant = fields.Char(
        string="Merchant",
        required=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
    )
    amount = fields.Monetary(
        string="Amount",
        default=0.0,
        required=True,
        currency_field='currency_id',
    )
    category = fields.Char(
        string="Category",
        required=True,
    )
    errors = fields.Char(
        string="Errors",
    )
    data = fields.Text(
        string="Raw JSON",
        required=True,
    )

    @api.depends('expense_date', 'amount', 'merchant')
    def _compute_name(self):
        for log in self:
            log.name = f"[{log.expense_date.strftime('%Y-%m-%d')}]({log.amount}) {log.merchant}"
