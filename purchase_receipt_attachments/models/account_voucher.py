from odoo import models, fields, api


class AccountVoucher(models.Model):

    _inherit = 'account.voucher'

    attachment_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'account.voucher'), ('type', '=', 'binary')],
        auto_join=True,
        string="Docs")

