#!/bin/bash

curl -X POST 'https://integrations.expensify.com/Integration-Server/ExpensifyIntegrations' \
    -d 'requestJobDescription={
        "type":"download",
        "credentials":{
            "partnerUserID":"aa_matt454357_gmail_com",
            "partnerUserSecret":"0217019ff522301572f050054b91c5e711a4d8dc"
        },
        "fileName":"myExportb3eb23c5-5d6f-4387-a846-99d7375c09f5.csv",
        "fileSystem":"integrationServer"
    }'
