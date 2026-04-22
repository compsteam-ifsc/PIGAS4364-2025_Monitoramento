let grafico = null;

// diaHorario pode chegar como:
// - string ISO "2025-04-22T10:30:00"  → substring(11,13) = hora
// - array [2025,4,22,10,30,0]         → index 3 = hora
function extrairHora(diaHorario) {
    if (Array.isArray(diaHorario)) {
        return String(diaHorario[3]).padStart(2, '0');
    } else if (typeof diaHorario === 'string' && diaHorario.length >= 13) {
        return diaHorario.substring(11, 13);
    }
    return null;
}

// primeiraEntrada / ultimaSaida chegam como "HH:mm" (já formatado pelo backend)
// OU como null → retorna '--:--'
function exibirHorario(valor) {
    if (!valor) return '--:--';
    // Já é "HH:mm" direto do backend novo, ou pode ser string ISO longa
    if (typeof valor === 'string') {
        if (valor.length === 5) return valor;           // "HH:mm"
        if (valor.length >= 16) return valor.substring(11, 16); // ISO full
    }
    if (Array.isArray(valor)) {
        const h = String(valor[3]).padStart(2, '0');
        const m = String(valor[4]).padStart(2, '0');
        return h + ':' + m;
    }
    return '--:--';
}

async function carregarGrafico(data) {
    if (!data) return;

    try {
        const response = await fetch(`/api/dashboard/filtrado?data=${data}`);
        if (!response.ok) throw new Error("Erro HTTP: " + response.status);

        const dados = await response.json();
        if (!Array.isArray(dados)) { console.error("Resposta invalida:", dados); return; }

        const mapaHoras = {};
        dados.forEach(item => {
            const hora = extrairHora(item.diaHorario);
            if (hora === null) return;
            mapaHoras[hora] = (mapaHoras[hora] || 0) + 1;
        });

        const horasOrdenadas = Object.keys(mapaHoras).sort((a, b) => parseInt(a) - parseInt(b));
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
                    hoverBackgroundColor: 'rgba(37, 99, 235, 0.35)',
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1e293b',
                        titleColor: '#94a3b8',
                        bodyColor: '#f8fafc',
                        padding: 12,
                        cornerRadius: 10,
                        callbacks: {
                            label: ctx => ` ${ctx.parsed.y} movimentações`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 13 } },
                        border: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(226,232,240,0.7)', drawBorder: false },
                        ticks: {
                            stepSize: 1,
                            color: '#94a3b8',
                            font: { size: 12 },
                            padding: 8
                        },
                        border: { display: false }
                    }
                }
            }
        });

    } catch (e) {
        console.error("Erro grafico:", e);
    }
}

async function carregarResumo(data) {
    const elEntradas       = document.getElementById("totalEntradas");
    const elPrimeira       = document.getElementById("primeiraEntrada");
    const elUltima         = document.getElementById("ultimaSaida");

    if (!data) {
        elEntradas.textContent = "--";
        elPrimeira.textContent = "--:--";
        elUltima.textContent   = "--:--";
        return;
    }

    try {
        const inicio = data + "T00:00:00";
        const fim    = data + "T23:59:59";

        const response = await fetch(`/api/dashboard/resumo?inicio=${inicio}&fim=${fim}`);
        if (!response.ok) throw new Error("Erro HTTP: " + response.status);

        const resumo = await response.json();

        elEntradas.textContent = (resumo.totalEntradas != null) ? resumo.totalEntradas : 0;
        elPrimeira.textContent = exibirHorario(resumo.primeiraEntrada);
        elUltima.textContent   = exibirHorario(resumo.ultimaSaida);

    } catch (e) {
        console.error("Erro resumo:", e);
    }
}

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