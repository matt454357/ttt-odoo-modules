from odoo import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    event_id = fields.Many2one(
        comodel_name='calendar.event',
        string='Event')
