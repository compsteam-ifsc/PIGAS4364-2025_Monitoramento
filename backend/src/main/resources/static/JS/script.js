let grafico = null;

// ---------------- UTIL ----------------

function extrairHora(diaHorario) {
    if (Array.isArray(diaHorario)) {
        return String(diaHorario[3]).padStart(2, '0');
    }

    if (typeof diaHorario === 'string') {
        if (diaHorario.includes("T") || diaHorario.includes(" ")) {
            return diaHorario.substring(11, 13);
        }
    }

    return null;
}

function exibirHorario(valor) {
    if (!valor) return '--:--';

    if (typeof valor === 'string') {
        if (valor.length === 5) return valor;
        if (valor.length >= 16) return valor.substring(11, 16);
    }

    if (Array.isArray(valor)) {
        const h = String(valor[3]).padStart(2, '0');
        const m = String(valor[4]).padStart(2, '0');
        return h + ':' + m;
    }

    return '--:--';
}

// ---------------- HEADER INTELIGENTE ----------------

function getAuthHeaders() {
    const token = localStorage.getItem("token");

    // Se tiver token → usa JWT
    if (token) {
        return {
            "Authorization": "Bearer " + token
        };
    }

    // Se não tiver → usa sessão (cookie automático)
    return {};
}

// ---------------- GRAFICO ----------------

async function carregarGrafico(data) {
    if (!data) return;

    try {
        const response = await fetch(`/api/dashboard/filtrado?data=${data}`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            console.error("Erro HTTP:", response.status);
            return;
        }

        const dados = await response.json();

        if (!Array.isArray(dados)) {
            console.error("Resposta inválida:", dados);
            return;
        }

        const mapaHoras = {};

        dados.forEach(item => {
            const hora = extrairHora(item.diaHorario);
            if (hora === null) return;
            mapaHoras[hora] = (mapaHoras[hora] || 0) + 1;
        });

        const horasOrdenadas = Object.keys(mapaHoras)
            .sort((a, b) => parseInt(a) - parseInt(b));

        const labels  = horasOrdenadas.map(h => h + ":00");
        const valores = horasOrdenadas.map(h => mapaHoras[h]);

        if (grafico) {
            grafico.data.labels = labels;
            grafico.data.datasets[0].data = valores;
            grafico.update();
            return;
        }

        const ctx = document.getElementById('barChart').getContext('2d');

        grafico = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    label: 'Fluxo por Hora',
                    data: valores,
                    backgroundColor: 'rgba(37, 99, 235, 0.18)',
                    borderColor: 'rgba(37, 99, 235, 0.85)',
                    borderWidth: 2,
                    borderRadius: 10,
                    borderSkipped: false,
                    hoverBackgroundColor: 'rgba(37, 99, 235, 0.35)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });

    } catch (e) {
        console.error("Erro gráfico:", e);
    }
}

// ---------------- RESUMO ----------------

async function carregarResumo(data) {

    const elEntradas = document.getElementById("totalEntradas");
    const elPrimeira = document.getElementById("primeiraEntrada");
    const elUltima   = document.getElementById("ultimaSaida");

    if (!data) {
        elEntradas.textContent = "--";
        elPrimeira.textContent = "--:--";
        elUltima.textContent   = "--:--";
        return;
    }

    try {
        const inicio = data + "T00:00:00";
        const fim    = data + "T23:59:59";

        const response = await fetch(`/api/dashboard/resumo?inicio=${inicio}&fim=${fim}`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            console.error("Erro HTTP:", response.status);
            return;
        }

        const resumo = await response.json();

        elEntradas.textContent = resumo.totalEntradas ?? 0;
        elPrimeira.textContent = exibirHorario(resumo.primeiraEntrada);
        elUltima.textContent   = exibirHorario(resumo.ultimaSaida);

    } catch (e) {
        console.error("Erro resumo:", e);
    }
}

// ---------------- INIT ----------------

window.onload = async () => {

    const inputData = document.getElementById("dataInput");

    const hoje = new Date().toLocaleDateString('en-CA');
    inputData.value = hoje;

    await carregarGrafico(hoje);
    await carregarResumo(hoje);

    inputData.addEventListener("change", async (e) => {
        await carregarGrafico(e.target.value);
        await carregarResumo(e.target.value);
    });

    setInterval(async () => {
        await carregarGrafico(inputData.value);
        await carregarResumo(inputData.value);
    }, 5000);
};