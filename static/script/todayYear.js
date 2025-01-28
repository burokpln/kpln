let today = new Date();
let year = today.getFullYear();
document.getElementById("yearToday").textContent = year;



window.onerror = function (message, source, lineno, colno, error) {
    console.error("JavaScript Error rev-1:", message, source, lineno, colno, error);
    sendErrorToServer({'from':'onerror', message, source, 'lineNo':lineno, 'colNo':colno, 'error':String(error) });
    return reloadPage();
};

window.addEventListener("error", function (event) {
    if (event.message) {
        console.error("JavaScript Error rev-2:", event.message);
    } else {
        console.error("Resource Error: Failed to load", event.target.src || event.target.href);
        sendErrorToServer({'url':document.URL,'from':'addEventListener.error', message: event.message || "Resource error", target: event.target.src || event.target.href });
    }
    return reloadPage();
}, true);

window.addEventListener("unhandledrejection", function (event) {
    console.error("Unhandled Promise Rejection:", event.reason, event);
    sendErrorToServer({'from':'addEventListener.unhandledrejection', error: event.reason, event: event });
    return reloadPage();
});

function sendErrorToServer(errorInfo) {
    fetch("/log-error", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({'url':document.URL, 'errorInfo':errorInfo})
    })
    .then(response => response.json())
    .then(data => {
        // return 0;
        return window.location.href = '/';
    })
}

function reloadPage() {
   //  return 0;
   return  window.location.href = '/';
}