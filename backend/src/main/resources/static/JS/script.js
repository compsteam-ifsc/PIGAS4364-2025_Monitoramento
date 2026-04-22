let grafico = null;

async function carregarGrafico(data) {
    if (!data) return;

    try {
        const response = await fetch(`/api/dashboard/filtrado?data=${data}`);

        if (!response.ok) {
            throw new Error("Erro HTTP: " + response.status);
        }

        const dados = await response.json();

        if (!Array.isArray(dados)) {
            console.error("Resposta inválida:", dados);
            return;
        }

        const mapaHoras = {};

        dados.forEach(item => {
            const hora = item.diaHorario.substring(11, 13); 

            if (!mapaHoras[hora]) {
                mapaHoras[hora] = 0;
            }

            mapaHoras[hora]++;
        });

        const labels = Object.keys(mapaHoras).map(h => h + ":00");
        const valores = Object.values(mapaHoras);

        const ctx = document.getElementById('barChart').getContext('2d');

        if (grafico) {
            grafico.data.labels = labels;
            grafico.data.datasets[0].data = valores;
            grafico.update();
            return;
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
                maintainAspectRatio: false
            }
        });

    } catch (e) {
        console.error("Erro gráfico:", e);
    }
}

async function carregarResumo(data) {
    if (!data) {
        document.getElementById("totalEntradas").textContent = "--";
        document.getElementById("primeiraEntrada").textContent = "--:--";
        document.getElementById("ultimaSaida").textContent = "--:--";
        return;
    }

    try {
        const inicio = data + "T00:00:00";
        const fim = data + "T23:59:59";

        const response = await fetch(`/api/dashboard/resumo?inicio=${inicio}&fim=${fim}`);

        const resumo = await response.json();

        document.getElementById("totalEntradas").textContent = resumo.totalEntradas ?? 0;
        document.getElementById("primeiraEntrada").textContent = resumo.primeiraEntrada ?? "--:--";
        document.getElementById("ultimaSaida").textContent = resumo.ultimaSaida ?? "--:--";

    } catch (e) {
        console.error("Erro resumo:", e);
    }
}

// INIT
window.onload = async () => {
    const inputData = document.getElementById("dataInput");

    const hoje = new Date().toLocaleDateString('en-CA');
    inputData.value = hoje;

    await carregarGrafico(hoje);
    await carregarResumo(hoje);
};

setInterval(async () => {
    const data = document.getElementById("dataInput").value;

    await carregarGrafico(data);
    await carregarResumo(data);

}, 3000);

document.getElementById("dataInput").addEventListener("change", async (e) => {
    const dataSelecionada = e.target.value;

    await carregarGrafico(dataSelecionada);
    await carregarResumo(dataSelecionada);
});