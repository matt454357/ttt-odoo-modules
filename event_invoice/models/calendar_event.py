from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools import is_html_empty
import re


class Meeting(models.Model):
    _inherit = 'calendar.event'

    invoice_line_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='event_id',
    )

    def _prepare_invoice_data(self, partner, product):
        self.ensure_one()

        journal = self.env['account.move'].with_context(
            default_move_type='out_invoice')._get_default_journal()
        if not journal:
            raise UserError(
                _('Please define an accounting sales journal for the '
                  'company %s (%s).') % (company.name, company.id))

        # parse event description for email
        email = False
        m = re.findall(r"Email: (.+?)<br>", self.description)
        if len(m) == 1:
            email = m[0] or False

        narration = self.description

        attendee = self.partner_ids and self.partner_ids[0]
        user = attendee and self.env['res.users'].search([('partner_id', '=', attendee.id)])
        invoice_user_id = user and user.id
        fpos = partner.property_account_position_id.id

        invoice_vals = {
            'ref': self.name,
            'invoice_date': self.start.date(),
            'invoice_date_due': self.start.date(),
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'partner_shipping_id': partner.id,
            # 'currency_id': currency.id,
            'narration': narration if not is_html_empty(narration) else '',
            'invoice_origin': self.name,
            'invoice_source_email': email,
            'invoice_line_ids': [],
            'fiscal_position_id': fpos and fpos.id or False,
            'invoice_user_id': invoice_user_id or self.user_id and self.user_id.id,
            'company_id': self.env.user.company_id.id,
            'journal_id': journal.id,
        }

        # account = product.property_account_income_id or \
        #     product.categ_id.property_account_income_categ_id
        account = product.product_tmpl_id.get_product_accounts(fiscal_pos=fpos)['income']
        if not account:
            raise UserError(
                'Please define income account for this product: "%s" (id:%d) '
                '- or for its category: "%s".') % (product.name,
                    product.id, product.categ_id.name)

        line_vals = {
            'name': product.name,
            'account_id': account.id,
            'price_unit': product.lst_price,
            'quantity': 1,
            'product_uom_id': product.uom_id.id,
            'product_id': product.id,
            'event_id': self.id,
        }
        balance = -product.lst_price
        line_vals.update({
            'debit': balance > 0.0 and balance or 0.0,
            'credit': balance < 0.0 and -balance or 0.0,
        })
        invoice_vals['invoice_line_ids'].append((0, 0, line_vals))

        return invoice_vals

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

        # get partner
        partner = self.env['res.partner'].search([('name', '=', partner_name)])
        if len(partner) > 1:
            raise UserError("Multiple partners with name %s" % partner_name)
        if len(partner) < 1:
            raise UserError(f"Partner {partner_name} not found")

        # get product
        product = self.env['product.product'].search(
            [('name', '=', product_name)], limit=1)
        if not product:
            raise UserError("Unknown product %s" % product_name)

        # create invoice and lines
        invoice_data = self[0]._prepare_invoice_data(partner, product)
        invoice = self.env['account.move'].create(invoice_data)

        # show the invoice
        # action = self.env.ref('account.action_invoice_tree1').read()[0]
        # form_view = [(self.env.ref('account.invoice_form').id, 'form')]
        # if 'views' in action:
        #     action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
        # else:
        #     action['views'] = form_view
        # action['res_id'] = invoice.id
        # return action

        return {
            'name': 'Invoice created',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'account.move',
            'view_id': self.env.ref('account.view_move_form').id,
            'target': 'current',
            'res_id': invoice.id,
            }
