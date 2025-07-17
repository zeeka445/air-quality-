const chartCtx = document.getElementById('chart').getContext('2d');
const chart = new Chart(chartCtx, {
    type: 'line',
    data: {
        labels: [],
        datasets: [
            {
                label: 'الحرارة',
                borderColor: 'red',
                data: [],
                fill: false
            },
            {
                label: 'الرطوبة',
                borderColor: 'blue',
                data: [],
                fill: false
            },
            {
                label: 'الغاز',
                borderColor: 'green',
                data: [],
                fill: false
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: false },
            x: { title: { display: true, text: "عدد القراءات" } }
        }
    }
});

function fetchData() {
    fetch('/data')
        .then(res => res.json())
        .then(data => {
            if (data.length > 0) {
                const last = data[data.length - 1];

                document.getElementById('temp').textContent = last.temp.toFixed(1);
                document.getElementById('hum').textContent = last.hum.toFixed(1);
                document.getElementById('gas').textContent = last.gas.toFixed(1);
                document.getElementById('quality').textContent = last.quality;

                // تنبيه
                const alertBox = document.getElementById('alertBox');
                if (last.alert) {
                    alertBox.style.display = 'block';
                    alertBox.textContent = last.alert;
                } else {
                    alertBox.style.display = 'none';
                }

                // الرسم البياني
                chart.data.labels = data.map((_, i) => i + 1);
                chart.data.datasets[0].data = data.map(d => d.temp);
                chart.data.datasets[1].data = data.map(d => d.hum);
                chart.data.datasets[2].data = data.map(d => d.gas);
                chart.update();

                // الجدول
                const tableBody = document.getElementById('tableBody');
                tableBody.innerHTML = '';
                data.slice(-10).reverse().forEach(d => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${d.timestamp}</td>
                        <td>${d.temp.toFixed(1)}</td>
                        <td>${d.hum.toFixed(1)}</td>
                        <td>${d.gas.toFixed(1)}</td>
                        <td>${d.quality}</td>
                    `;
                    tableBody.appendChild(tr);
                });
            }
        });
}

function exportToExcel() {
    fetch('/export')
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'air_quality_data.xlsx';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => console.error('Error:', error));
}

setInterval(fetchData, 2000);
fetchData();
