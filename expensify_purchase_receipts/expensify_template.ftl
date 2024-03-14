<#if addHeader == true>
    Merchant,Original Amount,Category,Report number,Expense number<#lt>
</#if>
<#assign reportNumber = 1>
<#assign expenseNumber = 1>
<#list reports as report>
    <#list report.transactionList as expense>
        ${expense.merchant},<#t>
        <#-- note: expense.amount prints the original amount only -->
        ${expense.amount},<#t>
        ${expense.category},<#t>
        ${reportNumber},<#t>
        ${receiptObject.url},<#t>
        ${expenseNumber}<#lt>
        <#assign expenseNumber = expenseNumber + 1>
    </#list>
    <#assign reportNumber = reportNumber + 1>
</#list>
