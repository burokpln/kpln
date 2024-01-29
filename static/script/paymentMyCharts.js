function paymentMyCharts(chart_type) {
        var existingChart = Chart.getChart("myChart");
                    if (existingChart) {
                      existingChart.destroy();
                    }

        fetch('/get-paymentMyCharts', {
            "headers": {
                'Content-Type': 'application/json'
            },
            "method": "POST",
            "body": JSON.stringify({
                'chart_type': chart_type
            })
        })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (!data.historic_data) {return}

                    var labels = [];
                    var values = [];

                    data.historic_data.forEach(function(entry) {
                        labels.push(entry.create_at);
                        values.push(entry.cur_bal);
                    });

//                    document.getElementById('myChart').style.display = "";
//                    document.getElementById('myChart').setAttribute("hidden", "");

                    // Get the canvas element
                    var ctx = document.getElementById('myChart').getContext('2d');

                    var existingChart = Chart.getChart("myChart");
                    if (existingChart) {
                      existingChart.destroy();
                    }

                const crossButtonDD = document.querySelector("#crossBtnDD");
                const dialogDD = document.querySelector("#diagram__dialog");

                crossButtonDD.addEventListener("click", closeDialogDD);

                function closeDialogDD() {
                    dialogDD.close();
                }

                // Create the chart
                var chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{
                            label: data.label,
                            data: values,
                            backgroundColor: 'rgba(0, 123, 255, 0.5)',
                            borderColor: 'rgba(0, 123, 255, 1)',
                            borderWidth: 1,
                            tension: 0.1
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: {
                                position: 'top',
                            },
                            title: {
                                display: true,
                                text: data.title
                            }
                        },
                        scales: {
                            //                                x: {
                            //                                    ticks: {
                            //                                        maxTicksLimit: 8
                            //                                    }
                            //                                }
                        },

                    }
                });
                //                    chart.options.scales.x.ticks.maxTicksLimit = 3; // Change this value to the desired number of values
                //                    chart.update()


                //                    const modalDialog = document.querySelector("#diagram__dialog");
                //                    modalDialog.addEventListener('click', function() {
                //                        // Hide the chart
                //                        chart.destroy();
                //                        modalDialog.close();
                //                    });
                const dialog = document.querySelector("#diagram__dialog");
                dialog.showModal();
//                return
            }
            else if (data.status === 'error') {
                alert(data.description)
            }
            else {
                window.location.href = '/payment-approval';
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
};