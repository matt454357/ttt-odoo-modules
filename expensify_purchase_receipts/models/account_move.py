from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    # create our own ref field for identifying expensify imports
    expensify_ref = fields.Char(
        string="Expensify Ref",
    )

    def action_post(self):
        # don't post purchase receipts without a vendor
        if self.move_type == 'in_receipt' and not self.partner_id:
            raise UserError("A vendor is required to post purchase receipts")
        res = super(AccountMove, self).action_post()
        return res
