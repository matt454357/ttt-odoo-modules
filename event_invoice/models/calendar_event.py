from odoo import models, fields, api
from odoo.exceptions import UserError
import re


class Meeting(models.Model):

    _inherit = 'calendar.event'

    invoice_line_ids = fields.One2many(
        comodel_name='account.invoice.line',
        inverse_name='event_id')

    def _prepare_invoice_data(self, partner):
        self.ensure_one()
        journal_id = (self.env['account.invoice'].default_get(
            ['journal_id'])['journal_id'])
        if not journal_id:
            raise UserError('Please define an accounting sales journal for '
                            'this company.')
        vinvoice = self.env['account.invoice'].new({'partner_id': partner.id,
                                                    'type': 'out_invoice'})
        # Get partner extra fields
        vinvoice._onchange_partner_id()
        invoice_vals = vinvoice._convert_to_write(vinvoice._cache)
        invoice_vals.update({
            'name': self.name,
            'origin': self.name,
            'type': 'out_invoice',
            'account_id': partner.property_account_receivable_id.id,
            'date_invoice': self.start.date(),
            'date_due': self.start.date(),
            'partner_shipping_id': partner.id,
            'journal_id': journal_id,
            'comment': self.description,
            'fiscal_position_id': partner.property_account_position_id.id,
            'company_id': self.env.user.company_id.id,
            'user_id': self.user_id and self.user_id.id,
        })
        return invoice_vals

    def _prepare_invoice_line_data(self, invoice, product):
        self.ensure_one()
        account = product.property_account_income_id or \
            product.categ_id.property_account_income_categ_id

        if not account:
            raise UserError(
                'Please define income account for this product: "%s" (id:%d) '
                '- or for its category: "%s".') % (self.product_id.name,
                    self.product_id.id, self.product_id.categ_id.name)

        line_vals = {
            'invoice_id': invoice.id,
            'name': product.name,
            'origin': self.name,
            'account_id': account.id,
            'price_unit': product.lst_price,
            'quantity': 1,
            'uom_id': product.uom_id.id,
            'product_id': product.id,
            'event_id': self.id,
        }
        return line_vals

    @api.multi
    def action_create_invoice(self):
        if len(set(self.mapped('name'))) != 1:
            raise UserError("You can only generate an invoice for one "
                            "or more calendar events with the same name.")
        # parse event name
        m = re.match(r'^(.+) \((.+)\)$', self[0].name)
        if not m or not len(m.groups()) == 2:
            raise UserError("Event name cannot be parsed:\n%s" % self[0].name)
        partner_name = m.group(1)
        product_name = m.group(2)

        # parse event description and update location
        for event in self:
            m = re.findall(r"^Address: (.+)$", event.description, re.MULTILINE)
            address = False
            if len(m) == 1:
                address = m[0] or False
            event.location = address

        # get partner
        partner = self.env['res.partner'].search([('name', '=', partner_name)])
        if len(partner) > 1:
            raise UserError("Multiple partners with name %s" % partner_name)

        # get product
        product = self.env['product.product'].search(
            [('name', '=', product_name)], limit=1)
        if not product:
            raise UserError("Unknown product %s" % product_name)

        # create invoice and lines
        invoice_data = self[0]._prepare_invoice_data(partner)
        invoice = self.env['account.invoice'].create(invoice_data)
        for rec in self:
            line_data = rec._prepare_invoice_line_data(invoice, product)
            self.env['account.invoice.line'].create(line_data)

        # show the invoice
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        form_view = [(self.env.ref('account.invoice_form').id, 'form')]
        if 'views' in action:
            action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        else:
            action['views'] = form_view
        action['res_id'] = invoice.id
        return action
