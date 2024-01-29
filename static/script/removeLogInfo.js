function removeLogInfo() {
    var element = document.getElementById('logInfo');
    if (element) {
        element.parentNode.removeChild(element);
    }
}