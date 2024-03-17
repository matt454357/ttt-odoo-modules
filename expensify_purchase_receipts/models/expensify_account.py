import requests
import json
import re
import base64
from urllib.parse import quote, quote_plus
from odoo import models, fields, api
from odoo.exceptions import UserError


RE_CATEGORY = re.compile(r'^(\d+)\..+$')

# this should work, but it doesn't
# TEMPLATE = """[
# <#list reports as report>
#     <#list report.transactionList as expense>
#         {
#             "accountEmail": "${report.accountEmail}",
#             "amount": "${expense.amount}",
#             "bank": "${expense.bank}",
#             "category": "${expense.category}",
#             "comment": "${expense.comment}",
#             "created": "${expense.created}",
#             "currency": "${expense.currency}",
#             "inserted": "${expense.inserted}",
#             "merchant": "${expense.merchant}",
#             "modifiedAmount": "${expense.modifiedAmount}",
#             "modifiedCreated": "${expense.modifiedCreated}",
#             "modifiedMerchant": "${expense.modifiedMerchant}",
#             "receiptFilename": "${expense.receiptFilename}",
#             "receiptID": "${expense.receiptID}",
#             "receiptObject.url": "${expense.receiptObject.url}",
#             "reimbursable": "${expense.reimbursable?string("true", "false")}",
#             "policyName": "${expense.policyName}",
#             "reportID": "${expense.reportID}",
#             "tag": "${expense.tag}",
#             "transactionID": "${expense.transactionID}",
#             "type": "${expense.type}",
#             "units.count": "${expense.units.count}",
#             "units.rate": "${expense.units.rate}",
#             "units.unit": "${expense.units.unit}"
#         }<#sep>,</#sep>
#     </#list><#sep>,</#sep>
# </#list>
# ]"""

# it appears that the expensify api has a buggy implementation of freemarker
# we sometimes end up with double commas (,,)
# these must be stripped before parsing the json
TEMPLATE = """[
<#list reports as report>
  <#list report.transactionList as expense>
    {
      "accountEmail": "${report.accountEmail}",
      "amount": "${expense.amount}",
      "bank": "${expense.bank}",
      "category": "${expense.category}",
      "comment": "${expense.comment}",
      "created": "${expense.created}",
      "currency": "${expense.currency}",
      "inserted": "${expense.inserted}",
      "merchant": "${expense.merchant}",
      "modifiedAmount": "${expense.modifiedAmount}",
      "modifiedCreated": "${expense.modifiedCreated}",
      "modifiedMerchant": "${expense.modifiedMerchant}",
      "receiptFilename": "${expense.receiptFilename}",
      "receiptID": "${expense.receiptID}",
      "receiptObject.url": "${expense.receiptObject.url}",
      "reimbursable": "${expense.reimbursable?string("true", "false")}",
      "policyName": "${expense.policyName}",
      "reportID": "${expense.reportID}",
      "tag": "${expense.tag}",
      "transactionID": "${expense.transactionID}",
      "type": "${expense.type}",
      "units.count": "${expense.units.count}",
      "units.rate": "${expense.units.rate}",
      "units.unit": "${expense.units.unit}"
    }<#sep>,,</#sep></#list><#sep>,</#sep></#list>]"""

class ExpensifyAccount(models.Model):
    _name = 'expensify.account'
    _description = "Expensify account info"

    name = fields.Char(
        string="Account Name",
        required=True,
    )
    user_id = fields.Char(
        string="User ID",
        required=True,
    )
    user_secret = fields.Char(
        string="Secret",
        required=True,
    )
    api_url = fields.Char(
        string="API URL",
        required=True,
    )
    start_date = fields.Datetime(
        string="Start Date",
        required=True,
        help="Won't import expensify expenses prior to this date",
    )
    last_import_date = fields.Datetime(
        string="Last Import",
    )
    import_errors = fields.Integer(
        string="Import Errors",
        required=True,
        default=0,
    )
    log_ids = fields.One2many(
        comodel_name='expensify.log',
        inverse_name="account_id",
        string="Import Log",
    )
    default_journal_id = fields.Many2one(
        comodel_name='account.journal',
        string="Default Journal",
        required=True,
    )

    def action_import_all(self):
        self.action_import(all=True)

    def action_import(self, all=False):
        self.ensure_one()

        # get report from expensify
        file_name = self.create_report(all=all)
        res = self.get_report_file(file_name)
        if res.status_code == 200 and len(res.text) < 4:
            raise UserError(f"No transactions were received")
        try:
            text = res.text.replace(',,', ',')
            text = text.replace(',]', ']')  # this happens on the first attempt to retrieve the report
            data = json.loads(text)
        except Exception as e:
            raise UserError(f"Failed to convert JSON report: {e}")

        # get existing expensify refs
        domain = [('move_type', '=', 'in_receipt'),
                  ('expensify_ref', '!=', False)]
        moves = self.env['account.move'].search(domain)
        expensify_refs = moves.mapped('expensify_ref')

        # validate data
        error_count = 0
        log_entries = []
        for exp in data:
            errors = []
            exp_log = {
                'account_id': self.id,
                'log_timestamp': fields.Datetime.now(),
                'success': False,
                'account_mail': exp['accountEmail'],
                'expense_date': exp['modifiedCreated'] or exp['created'],
                'merchant': exp['modifiedMerchant'] or exp['merchant'],
                'category': exp['category'],
                'data': json.dumps(exp),
            }

            # validate amount
            amount = float(exp['modifiedAmount'] or exp['amount'] or 0.0) / 100.0
            exp['amount'] = amount

            # validate GL account
            account_id = None
            account_match = RE_CATEGORY.match(exp['category'])
            if account_match:
                dom = [('code', '=', account_match.group(1))]
                account_id = self.env['account.account'].search(dom, limit=1)
                if account_id:
                    exp['account_id'] = account_id.id
            if not exp.get('account_id'):
                errors.append('Invalid Account')

            # validate merchant
            dom = [('name', 'ilike', exp_log['merchant'])]
            partner_id = self.env['res.partner'].search(dom, limit=1)
            if partner_id:
                if partner_id.parent_id:
                    exp['partner_id'] = partner_id.parent_id.id
                else:
                    exp['partner_id'] = partner_id.id
            if not exp.get('partner_id'):
                errors.append('Unmatched Merchant')

            # prepare account move data
            if amount > 0.0:
                debit = amount
                credit = 0.0
                move_type = 'in_receipt'
            else:
                debit = 0.0
                credit = -amount
                move_type = 'in_refund'

            vals = {
                'move_type': move_type,
                'partner_id': exp['partner_id'],
                'partner_shipping_id': exp['partner_id'],
                'invoice_date': exp['modifiedCreated'] or exp['created'],
                'invoice_date_due': exp['modifiedCreated'] or exp['created'],
                'company_id': self.env.user.company_id.id,
                'journal_id': self.default_journal_id.id,
                'narration': f"Expensify source: {exp['bank'] or 'Cash'}",
                'expensify_ref': exp['transactionID'],
                'invoice_line_ids': [(0, 0, {
                    'name': account_id.name,
                    'account_id': exp['account_id'],
                    'quantity': 1.0,
                    'discount': 0.0,
                    'price_unit': abs(amount),
                    'debit': debit,
                    'credit': credit,
                })],
            }
            exp['move_vals'] = vals

            # check for pre-existing import
            if exp['transactionID'] in expensify_refs:
                errors.append('Already Imported')

            if errors:
                error_count += 1
                exp_log['errors'] = ", ".join(errors)

            # add log entry
            log_entries.append(exp_log)

        if not error_count:
            # create Purchase Receipts
            for exp in data:
                move_vals = exp['move_vals']
                receipt = self.env['account.move'].create(move_vals)

                # attach the receipt image
                if exp['receiptObject.url']:
                    response = requests.get(exp['receiptObject.url'])
                    datas = base64.b64encode(response.content).decode('ascii')
                    if response.status_code == 200:
                        vals = {
                            'name': exp['receiptFilename'],
                            'res_model': 'account.move',
                            'res_id': receipt.id,
                            'type': 'binary',
                            'datas': datas
                        }
                        self.env['ir.attachment'].create(vals)

                # post the purchase receipt
                receipt.action_post()

            # mark log entries as successful
            for exp_log in log_entries:
                exp_log['success'] = True

            msg_type = 'notification'
            msg_title = 'Notification'
            msg_message = f"Imported {len(data)} transactions."

        else:
            msg_type = 'warning'
            msg_title = 'Warning'
            msg_message = (f"Encountered {error_count} errors, while trying to import {len(data)} transactions. No transactions"
                           f" were imported. See expensify logs for details.")

        self.import_errors = error_count

        # write log entries
        for exp_log in log_entries:
            self.log_ids.create(exp_log)
        self.last_import_date = fields.Datetime.now()

        return {
            'warning': {
                'type': msg_type,
                'title': msg_title,
                'message': msg_message,
            }
        }

    def create_report(self, all=False):
        msg = {
            "type": "file",
            "credentials": {
                "partnerUserID": self.user_id,
                "partnerUserSecret": self.user_secret,
            },
            "onReceive": {
                "immediateResponse": ["returnRandomFileName"],
            },
            "inputSettings": {
                "type": "combinedReportData",
                "filters": {
                    "startDate": self.start_date.strftime("%Y-%m-%d"),
                },
            },
            "outputSettings": {
                "fileExtension": "json",
                "fileBasename": "myExport",
            },
            "onFinish": [
                {"actionName": "markAsExported", "label": "Expensify Export"},
            ]
        }

        if not all:
            msg['inputSettings']['filters']['markedAsExported'] = \
                "Expensify Export"

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = ("requestJobDescription=" + json.dumps(msg, indent=4) +
                "&template=" + quote(TEMPLATE))
        response = requests.post(
            self.api_url,
            headers=headers,
            data=data,
        )
        if 'responseCode' in response.text:
            raise UserError(f"Request failed ({response.text})")
        return response.text

    def get_report_file(self, file_name):
        msg = {
            "type": "download",
            "credentials": {
                "partnerUserID": self.user_id,
                "partnerUserSecret": self.user_secret,
            },
            "fileName": file_name,
            "fileSystem": "integrationServer",
        }
        data = {
            "requestJobDescription": json.dumps(msg, indent=4),
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(
            self.api_url,
            headers=headers,
            data=data,
        )
        return response
