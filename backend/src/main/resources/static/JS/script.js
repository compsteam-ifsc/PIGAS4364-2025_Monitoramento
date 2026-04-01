let grafico = null;

async function carregarGrafico(data = null) {
    let url = '/dashboard/dados';

    if (data) {
        url = `/dashboard/filtrado?data=${data}`;
    }

    const response = await fetch(url);
    const dados = await response.json();

    console.log(dados);

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
                data: valores
            }]

        },
        options: {
        responsive: true,
        maintainAspectRatio: false
    }
    });
}


window.onload = () => carregarGrafico();


document.getElementById("dataInput")
    .addEventListener("change", (e) => {
        carregarGrafico(e.target.value);
    });