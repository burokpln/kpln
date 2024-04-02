function hideFullCardInfo() {
    var fullCardInfo = document.getElementById('ctr_full_card_div');
    var fullCardInfoButton = document.getElementById('ctr_hide_full_card_info');
    var miniCardInfo = document.getElementById('ctr_mini_card_div');
    fullCardInfoButton.hidden = true;
    fullCardInfo.hidden = true;
    miniCardInfo.hidden = false;
}

function showFullCardInfo() {
    var fullCardInfo = document.getElementById('ctr_full_card_div');
    var fullCardInfoButton = document.getElementById('ctr_hide_full_card_info');
    var miniCardInfo = document.getElementById('ctr_mini_card_div');
    fullCardInfoButton.hidden = false;
    fullCardInfo.hidden = false;
    miniCardInfo.hidden = true;
}



function getContractCard(button) {
    var td_0 = button.closest('tr').getElementsByTagName("td")[0];
    var contract_id = td_0.dataset.sort;
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    window.open(`/contracts-list/card/${contract_id}`, '_blank');
};

function selectCheckbox(chb) {
    var curCheckbox = button.closest('tr').getElementsByTagName("td")[0];

}
