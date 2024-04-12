$(document).ready(function() {
    if (document.getElementById('cash_inflow__money')) {
        document.getElementById('cash_inflow__money').addEventListener('change', function() {
            numberWithSpaces(event, ' ₽');
        });
    }
    if (document.getElementById('payment_sum')) {
        document.getElementById('payment_sum').addEventListener('change', function() {
            numberWithSpaces(event, ' ₽');
        });
    }
});

function numberWithSpaces(e, string) {
  const regExp = new RegExp(string, "g");
  const parts = e.target.value
    .replace(regExp, "")
    .replace(/[.]/g, ',')
    .replace(/[^0-9,]/g, "")
    .split(".");
  if (parts[0].indexOf(",") != "-1") {
    parts[0] = parts[0].substring(0, parts[0].indexOf(",") + 3);
  }

  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  e.target.value = parts.join(".") + string;
}