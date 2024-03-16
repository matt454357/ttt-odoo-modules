from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'account.move'), ('type', '=', 'binary')],
        auto_join=True,
        string="Docs",
    )

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    attachment_ids = fields.One2many(
        related='move_id.attachment_ids',
        auto_join=True,
        string="Docs",
    )
    account_type_id = fields.Many2one(
        related='account_id.user_type_id',
        auto_join=True,
        string="Account Type",
    )
    account_tag_ids = fields.Many2many(
        related='account_id.tag_ids',
        auto_join=True,
        string="Account Tags",
    )
