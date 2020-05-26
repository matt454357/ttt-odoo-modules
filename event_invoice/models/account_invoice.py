from odoo import models, fields, api


class InvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    event_id = fields.Many2one(
        comodel_name='calendar.event',
        string='Event')

    date_invoice = fields.Date(
        related='invoice_id.date_invoice',
        string='Invoice Date')
