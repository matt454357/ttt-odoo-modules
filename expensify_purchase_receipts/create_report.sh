#!/bin/bash

curl -X POST 'https://integrations.expensify.com/Integration-Server/ExpensifyIntegrations' \
    -d 'requestJobDescription={
        "type":"file",
        "credentials":{
            "partnerUserID":"aa_matt454357_gmail_com",
            "partnerUserSecret":"0217019ff522301572f050054b91c5e711a4d8dc"
        },
        "onReceive":{
            "immediateResponse":["returnRandomFileName"]
        },
        "inputSettings":{
            "type":"combinedReportData",
            "filters":{
                "startDate":"2023-01-01",
            }
        },
        "outputSettings":{
            "fileExtension":"csv",
            "fileBasename":"myExport"
        },
    }' \
    --data-urlencode 'template@expensify_template.ftl'
echo "\n"
