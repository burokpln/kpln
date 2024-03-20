//Окно подтверждения действия
const verificationDialog = document.getElementById('verif_dialog_empl');
//Кнопка ОК
const okBtn = document.getElementById('verif_dialog_empl__ok');

const logOutBtn = document.getElementById('logOut');
const changePasBtn = document.getElementById('change_password_form__button');

const paymentForm = document.getElementById('paymentForm');
const submit_button_in_form = document.getElementById('submitButton');

const annulEditBtn = document.getElementById('annul__edit_btn_i');
const annulApprovalEditBtn = document.getElementById('annul_approval__edit_btn_i');
const saveEditBtn = document.getElementById('save__edit_btn_i');

const hideDialog = () => {
    verificationDialog.close();
};

const showDialogDSB = () => {
    verificationDialog.showModal();
    paragraphQuestion.id = 'pqDSB'
};

const showDialogAEB = () => {
    verificationDialog.showModal();
    paragraphQuestion.id = 'pqAEB'
};

const showDialogAPEB = () => {
    verificationDialog.showModal();
    paragraphQuestion.id = 'pqAPEB'
};

const showDialogSEB = () => {
    verificationDialog.showModal();
    paragraphQuestion.id = 'pqSEB'
};

const showDialogLogOut = () => {
    verificationDialog.showModal();
    paragraphQuestion.id = 'logOut'
};

const showDialogChangePas = () => {
    verificationDialog.showModal();
    paragraphQuestion.id = 'changePas'
};

logOutBtn? logOutBtn.addEventListener('click', showDialogLogOut): 1;

changePasBtn? changePasBtn.addEventListener('click', showDialogChangePas): 1;

submit_button_in_form? submit_button_in_form.addEventListener('click', showDialogDSB): 1;

cancelDialogBtn? cancelDialogBtn.addEventListener('click', hideDialog): 1;

annulEditBtn? annulEditBtn.addEventListener('click', showDialogAEB): 1;

annulApprovalEditBtn? annulApprovalEditBtn.addEventListener('click', showDialogAPEB): 1;

saveEditBtn? saveEditBtn.addEventListener('click', showDialogSEB): 1;

nextDialogBtn? nextDialogBtn.addEventListener('click', function () {

    // Нажата кнопка отправить и подтверждён выбор
    if (paragraphQuestion.id === 'pqDSB') {
        paymentForm.submit();

    } else if (paragraphQuestion.id === 'pqAEB') {
        annulPayment();
    } else if (paragraphQuestion.id === 'pqAPEB') {
        annulApproval();
    } else if (paragraphQuestion.id === 'pqSEB') {
        savePayment();
    } else if (paragraphQuestion.id === 'logOut') {
        logOut();
    } else if (paragraphQuestion.id === 'changePas') {
        changePas();
    }
}): 1;