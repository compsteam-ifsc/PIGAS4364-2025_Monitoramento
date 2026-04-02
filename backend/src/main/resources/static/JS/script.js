let grafico = null;

async function carregarGrafico(data) {
    if (!data) return;

    const url = `/dashboard/filtrado?data=${data}`;

    const response = await fetch(url);
    const dados = await response.json();

    const labels = dados.map(item => item[0] + ":00");
    const valores = dados.map(item => item[1]);

    const ctx = document.getElementById('barChart').getContext('2d');

    if (grafico) {
        grafico.destroy();
    }

    grafico = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Fluxo por Hora',
                data: valores,
                backgroundColor: 'rgba(59, 130, 246, 0.45)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 2,
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#1a1d23',
                        font: {
                            size: 14,
                            weight: '600'
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: '#6b7280'
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: '#6b7280',
                        precision: 0
                    }
                }
            }
        }
    });
}

async function carregarResumo(data) {
    if (!data) {
        document.getElementById("totalEntradas").textContent = "--";
        document.getElementById("primeiraEntrada").textContent = "--:--";
        document.getElementById("ultimaSaida").textContent = "--:--";
        return;
    }

    const response = await fetch(`/dashboard/resumo?data=${data}`);
    const resumo = await response.json();

    document.getElementById("totalEntradas").textContent = resumo.totalEntradas ?? 0;
    document.getElementById("primeiraEntrada").textContent = resumo.primeiraEntrada ?? "--:--";
    document.getElementById("ultimaSaida").textContent = resumo.ultimaSaida ?? "--:--";
}

window.onload = async () => {
    const inputData = document.getElementById("dataInput");

    // pega a data de hoje no formato YYYY-MM-DD
    const hoje = new Date().toLocaleDateString('en-CA');

    // preenche o input com a data de hoje
    inputData.value = hoje;

    // carrega gráfico e resumo automaticamente no login
    await carregarGrafico(hoje);
    await carregarResumo(hoje);
};

document.getElementById("dataInput").addEventListener("change", async (e) => {
    const dataSelecionada = e.target.value;

    await carregarGrafico(dataSelecionada);
    await carregarResumo(dataSelecionada);
});