import requests
import json
import csv
import os
from urllib.parse import quote, quote_plus
from pprint import pprint


# TEMPLATE = """
# <#if addHeader == true>
#     Merchant,Original Amount,Category,Report number,Expense number<#lt>
# </#if>
# <#assign reportNumber = 1>
# <#assign expenseNumber = 1>
# <#list reports as report>
#     <#list report.transactionList as expense>
#         ${expense.merchant},<#t>
#         <#-- note: expense.amount prints the original amount only -->
#         ${expense.amount},<#t>
#         ${expense.category},<#t>
#         ${reportNumber},<#t>
#         ${expenseNumber}<#lt>
#         <#assign expenseNumber = expenseNumber + 1>
#     </#list>
#     <#assign reportNumber = reportNumber + 1>
# </#list>
# """

TEMPLATE = """[
<#list reports as report>
    <#list report.transactionList as expense>
        {<#lt>
            "report.accountEmail": "${report.accountEmail}",<#lt>
            "expense.amount": "${expense.amount}",<#lt>
            "expense.bank": "${expense.bank}",<#lt>
            "expense.category": "${expense.category}",<#lt>
            "expense.comment": "${expense.comment}",<#lt>
            "expense.created": "${expense.created}",<#lt>
            "expense.currency": "${expense.currency}",<#lt>
            "expense.inserted": "${expense.inserted}",<#lt>
            "expense.merchant": "${expense.merchant}",<#lt>
            "expense.modifiedAmount": "${expense.modifiedAmount}",<#lt>
            "expense.modifiedCreated": "${expense.modifiedCreated}",<#lt>
            "expense.modifiedMerchant": "${expense.modifiedMerchant}",<#lt>
            "expense.receiptFilename": "${expense.receiptFilename}",<#lt>
            "expense.receiptID": "${expense.receiptID}",<#lt>
            "expense.receiptObject.url": "${expense.receiptObject.url}",<#lt>
            "expense.reimbursable": "${expense.reimbursable}",<#lt>
            "expense.policyName": "${expense.policyName}",<#lt>
            "expense.reportID": "${expense.reportID}",<#lt>
            "expense.tag": "${expense.tag}",<#lt>
            "expense.transactionID": "${expense.transactionID}",<#lt>
            "expense.type": "${expense.type}",<#lt>
            "expense.units.count": "${expense.units.count}",<#lt>
            "expense.units.rate": "${expense.units.rate}",<#lt>
            "expense.units.unit": "${expense.units.unit}"<#lt>
        }<#sep>,</#sep><#lt>
    </#list><#sep>,</#sep>
</#list>
]"""

class Expensify:
    apiurl = "https://integrations.expensify.com/Integration-Server/ExpensifyIntegrations"
    user = "..."
    secret = "..."
    policy_id = "..."
    temp_file = "temp.csv"
    admin_file = "admins.txt"

    def __init__(self, user, secret, policy_id):
        self.user = user
        self.secret = secret
        self.policy_id = policy_id

    def get_base_message(self, start_date="2023-01-01", end_date="2023-01-31") -> dict:
        data = {
            "type": "file",
            "credentials": {
                "partnerUserID": self.user,
                "partnerUserSecret": self.secret,
            },
            "onReceive": {
                "immediateResponse": ["returnRandomFileName"],
            },
            "inputSettings": {
                "type": "combinedReportData",
                "filters": {
                    "startDate": start_date,
                    "markedAsExported": "Expensify Export",
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
        return data

    def create_report(self, msg):
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = "requestJobDescription=" + json.dumps(msg, indent=4) + "&template=" + quote(TEMPLATE)
        response = requests.post(
            self.apiurl,
            headers=headers,
            data=data,
        )
        if 'responseCode' in response.text:
            raise f"request failed ({response['responseCode']}): {response['responseMessage']}"
        return response.text

    def get_file(self, file_name):
        msg = {
            "type": "download",
            "credentials": {
                "partnerUserID": self.user,
                "partnerUserSecret": self.secret,
            },
            "fileName": file_name,
            "fileSystem": "integrationServer",
        }
        data = {
            "requestJobDescription": json.dumps(msg, indent=4),
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(
            self.apiurl,
            headers=headers,
            data=data,
        )
        return response
