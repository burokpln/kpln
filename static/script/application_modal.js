function getModal(paymentId = null) {
    var page_url = document.URL.substring(document.URL.lastIndexOf('/') + 1);
    fetch(`/get_card_payment/${page_url}/${paymentId}`)
        .then(response => response.json())
        .then(data => {
            const dialog = document.querySelector("#payment-approval__dialog");

            document.getElementById('payment_id').textContent = data.payment['payment_id'];
            document.getElementById('payment_number').textContent = data.payment['payment_number'];

            document.getElementById('basis_of_payment').textContent = data.payment['basis_of_payment'];
            document.getElementById('basis_of_payment').dataset.value = data.payment['basis_of_payment'];

            const select = document.getElementById('responsible');
            document.getElementById('responsible').dataset.value = data.payment['user_id'].toString();
            for (let i = 0; i < select.length; i++) {
                if (select[i].value === data.payment['user_id'].toString()) select[i].selected = true;
            }

            const select2 = document.getElementById('cost_items');
            document.getElementById('cost_items').dataset.value = data.payment['cost_item_id'].toString();
            for (let i = 0; i < select2.length; i++) {
                if (select2[i].value.split('-@@@-')[1] === data.payment['cost_item_id'].toString()) {
                    select2[i].selected = true;

                    if (select2[i].value.split('-@@@-')[0] === 'Субподрядчики') {
                        document.getElementById("objects_name_div").style.display = "flex";
                        document.getElementById("objects_name").required = true;
                    }
                    else if (select2[i].value.split('-@@@-')[0] !== 'Субподрядчики') {
                        document.getElementById("objects_name_div").style.display = "none";
                        document.getElementById("objects_name").required = false;
                    }
                }
            }

            const select3 = document.getElementById('objects_name');
            document.getElementById('objects_name').dataset.value = data.payment['object_id'].toString();
            for (let i = 0; i < select3.length; i++) {
                if (select3[i].value === data.payment['object_id'].toString()) select3[i].selected = true;
            }

            document.getElementById('payment_description').textContent = data.payment['payment_description'];
            document.getElementById('payment_description').dataset.value = data.payment['payment_description'];

            document.getElementById('partners').value = data.payment['partner'];
            document.getElementById('partners').dataset.value = data.payment['partner'];

            document.getElementById('payment_due_date').value = data.payment['payment_due_date'];
            document.getElementById('payment_due_date').dataset.value = data.payment['payment_due_date'];

            const select4 = document.getElementById('our_company');
            document.getElementById('our_company').dataset.value = data.payment['contractor_id'].toString();
            for (let i = 0; i < select4.length; i++) {
                if (select4[i].value === data.payment['contractor_id'].toString()) select4[i].selected = true;
            }

            document.getElementById('payment_sum').value = data.payment['payment_sum_rub'];
            document.getElementById('payment_sum').dataset.value = data.payment['payment_sum_rub'];

            document.getElementById('sum_unapproved').value = data.payment['unapproved_sum_rub'];
            document.getElementById('sum_unapproved').dataset.value = data.payment['unapproved_sum'];

            document.getElementById('sum_approval').value = data.payment['unpaid_approval_sum_rub'];
            document.getElementById('sum_approval').dataset.value = data.payment['unpaid_approval_sum'];

            document.getElementById('paymentFullStatus').checked = data.payment['payment_full_agreed_status'];
            document.getElementById('paymentFullStatus').dataset.value = data.payment['payment_full_agreed_status'];

            document.getElementById('unpaid_approval_sum').textContent = data.payment['approval_to_pay_sum_rub'];

            var bodyRef = document.getElementById('paid_history-table').getElementsByTagName('tbody')[0];
            bodyRef.innerHTML = ''

            if (data.paid.length) {
                let history_table = document.getElementById('history_tb');
                for (let i = 0; i < data.paid.length; i++) {
                    let newRow = document.createElement("tr");

                    let newCell1 = document.createElement("td");
                    newCell1.innerHTML = data.paid[i][1];

                    let newCell2 = document.createElement("td");
                    newCell2.innerHTML = data.paid[i][3];

                    let newCell3 = document.createElement("td");
                    newCell3.innerHTML = data.paid[i][5];

                    newRow.appendChild(newCell1);
                    newRow.appendChild(newCell2);
                    newRow.appendChild(newCell3);

                    history_table.appendChild(newRow);
                }

                document.getElementById('historic_paid_sum').textContent = data.paid[0][6];
            }
            else {
                document.getElementById('historic_paid_sum').textContent = 0;
            }

            var logDPage = document.getElementById('logDPage__content__text');
            logDPage.innerHTML = ''
            for (var i = 0; i < data.logs.length; i++) {
                const entry = document.createElement("p");
                entry.innerHTML = `
                    >> <span class="logTime"><span class="logTimeBold">${data.logs[i][0]}</span> ${data.logs[i][1]}:</span>
                    ${data.logs[i][2]}. ${data.logs[i][3]}.
                    <span class="logCash"><span class="logCashPay">${data.logs[i][4]}</span> </span>
                `;
                logDPage.appendChild(entry);
            }

            var title = `
- Заявка закроется,
- Несогласованный остаток (${data.payment['unapproved_sum_rub']}) удалится,
- Неоплаченный согласованный остаток (${data.payment['approval_to_pay_sum_rub']}) останется на листе ОПЛАТА`
            document.getElementById("annul__edit_btn_i").setAttribute("title", title)

            var title = `
- Заявка НЕ закроется,
- Неоплаченный согласованный остаток (${data.payment['approval_to_pay_sum_rub']}) удалится
- Остаток к оплате увеличится на (${data.payment['approval_to_pay_sum_rub']})`
            document.getElementById("annul_approval__edit_btn_i").setAttribute("title", title)

            if (data.user_role == '6' || page_url == 'payment-pay') {
                select.classList.add("input_ro");
                select.disabled = true;
                select2.classList.add("input_ro");
                select2.disabled = true;
                select3.classList.add("input_ro");
                select3.disabled = true;


                document.getElementById('payment_sum').classList.add("input_ro");
                document.getElementById('payment_sum').disabled = true;

                document.getElementById('sum_unapproved').classList.add("input_ro");

                document.getElementById('sum_approval').classList.add("input_ro");
                document.getElementById('sum_approval').disabled = true;

                document.getElementById('paymentFullStatus').classList.add("input_ro");
                document.getElementById('paymentFullStatus').disabled = true;

                document.getElementById('annul__edit_btn_i').disabled = true;
                document.getElementById('annul_approval__edit_btn_i').disabled = true;
                document.getElementById('annul__edit_btn_i').style.visibility = 'hidden';
                document.getElementById('annul_approval__edit_btn_i').style.visibility = 'hidden';

            }
            dialog.showModal();

        })
        .catch(error => {
            console.error('Error:', error);
        });
};
