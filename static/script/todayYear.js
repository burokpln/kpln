let today = new Date();
let year = today.getFullYear();
document.getElementById("yearToday").textContent = year;



window.onerror = function (message, source, lineno, colno, error) {
    console.error("JavaScript Error:", message, source, lineno, colno, error);
    sendErrorToServer({ message, source, lineno, colno, error });
    return true;
};

window.addEventListener("error", function (event) {
    if (event.message) {
        console.error("JavaScript Error:", event.message);
    } else {
        console.error("Resource Error: Failed to load", event.target.src || event.target.href);
    }
    sendErrorToServer({ message: event.message || "Resource error", target: event.target.src || event.target.href });
}, true);

window.addEventListener("unhandledrejection", function (event) {
    console.error("Unhandled Promise Rejection:", event.reason);
    sendErrorToServer({ error: event.reason });
});

function sendErrorToServer(errorInfo) {
    console.log("      sendErrorToServer:", errorInfo);
    alert(errorInfo);
    // fetch("/log-error", {
    //     method: "POST",
    //     headers: {
    //         "Content-Type": "application/json"
    //     },
    //     body: JSON.stringify(errorInfo)
    // });
}
