async function carregarGraficoFluxoHora() {
    try {
        const response = await fetch('/dashboard/dados');
        const dados = await response.json();

        console.log("Dados recebidos:", dados);

        const labels = dados.map(item => item[0] + ":00");
        const valores = dados.map(item => item[1]);

        const ctx = document.getElementById('barChart').getContext('2d');

        new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Fluxo por Hora',
                    data: valores,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Movimentação da Biblioteca por Hora'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Quantidade de Registros'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Horário'
                        }
                    }
                }
            }
        });

    } catch (error) {
        console.error('Erro ao carregar gráfico:', error);
    }
}

window.onload = carregarGraficoFluxoHora;