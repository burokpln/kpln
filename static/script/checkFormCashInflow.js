function checkFormCashInflow() {
    var CICompany = document.getElementById('cash_inflow__company').value;
    var CIType = document.getElementById('cash_inflow__type').value.split('-@@@-')[0];
    var CIMoney = document.getElementById('cash_inflow__money').value;
    var CIDescription = document.getElementById('cash_inflow__description').value;
    var CITransferCompany = document.getElementById('cash_inflow__transfer_company').value;
    var field3_1 = parseFloat(CIMoney.replaceAll('₽', '').replaceAll(" ", "").replaceAll(" ", "").replaceAll(",", "."))

    if (CIType == 4) {
        document.getElementById("cash_inflow__hidden_label").style.display = "flex";
        document.getElementById("cash_inflow__transfer_company").required = true;
        document.getElementById("cash_inflow__description_wrapper").style.display = "none";
        document.getElementById("cash_inflow__description").required = false;
        $("#cash_inflow__company_label").text("Откуда переводим")
    }
    else if (!CITransferCompany) {
        CITransferCompany = "пусто"
    }
    if (CIType != 4) {
        document.getElementById("cash_inflow__hidden_label").style.display = "none";
        document.getElementById("cash_inflow__transfer_company").required = false;
        document.getElementById("cash_inflow__description_wrapper").style.display = "flex";
        document.getElementById("cash_inflow__description").required = true;
        $("#cash_inflow__company_label").text("Компания")
    }
    else if (!CIDescription) {
        CIDescription = "пусто"
    }

    if (CICompany !== '' && CIType !== '' && CIMoney !== '' && CIDescription !== '' && CITransferCompany !== '' && field3_1) {
        document.getElementById('submit_button_in_form').disabled = false;
    } else {
        document.getElementById('submit_button_in_form').disabled = true;
    }
}