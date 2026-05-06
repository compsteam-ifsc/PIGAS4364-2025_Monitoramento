let grafico = null;

// ---------------- BOTÃO ----------------

function alternarRelatorio() {
    const path = window.location.pathname;

    if (path.includes("/Grafico/Diario")) {
        window.location.href = "/Grafico/Semanal";
    } else {
        window.location.href = "/Grafico/Diario";
    }
}

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

// ---------------- AUTH ----------------

function getAuthHeaders() {
    const token = localStorage.getItem("token");
    return token ? { "Authorization": "Bearer " + token } : {};
}

// ---------------- GRÁFICO ----------------

async function carregarGrafico(data, horaInicio, horaFim) {
    if (!data) return;

    try {
        const url = `/api/dashboard/filtrado?data=${data}&horaInicio=${horaInicio}&horaFim=${horaFim}`;
        const response = await fetch(url, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            console.error("Erro HTTP:", response.status);
            return;
        }

        const dados = await response.json();

        const mapaHoras = {};

        dados.forEach(item => {
            const hora = extrairHora(item.diaHorario);
            if (hora === null) return;
            mapaHoras[hora] = (mapaHoras[hora] || 0) + 1;
        });

        // 🔥 AQUI: força TODAS as horas
        const labels = [];
        const valores = [];

        for (let h = 0; h <= 23; h++) {
            const horaStr = String(h).padStart(2, '0');

            // respeita filtro selecionado
            if (h < parseInt(horaInicio) || h > parseInt(horaFim)) continue;

            labels.push(horaStr + ":00");
            valores.push(mapaHoras[horaStr] || 0);
        }

        const ctx = document.getElementById('barChart')?.getContext('2d');
        if (!ctx) return;

        if (grafico) {
            grafico.data.labels = labels;
            grafico.data.datasets[0].data = valores;
            grafico.update();
            return;
        }

        grafico = new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: 'Fluxo por Hora',
                    data: valores,
                    backgroundColor: 'rgba(37, 99, 235, 0.18)',
                    borderColor: 'rgba(37, 99, 235, 0.85)',
                    borderWidth: 2,
                    borderRadius: 10,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: { grid: { display: false } },
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

async function carregarResumo(data, horaInicio, horaFim) {

    const elEntradas  = document.getElementById("totalEntradas");
    const elPrimeira  = document.getElementById("primeiraEntrada");
    const elUltima    = document.getElementById("ultimaSaida");
    const elPresentes = document.getElementById("pessoasPresentes");

    if (!data) return;

    try {
        const inicio = `${data}T${String(horaInicio).padStart(2,'0')}:00:00`;
        const fim    = `${data}T${String(horaFim).padStart(2,'0')}:59:59`;

        const response = await fetch(`/api/dashboard/resumo?inicio=${inicio}&fim=${fim}`, {
            headers: getAuthHeaders()
        });

        if (!response.ok) {
            console.error("Erro HTTP:", response.status);
            return;
        }

        const resumo = await response.json();

        elEntradas.textContent  = resumo.totalEntradas ?? 0;
        elPrimeira.textContent  = exibirHorario(resumo.primeiraEntrada);
        elUltima.textContent    = exibirHorario(resumo.ultimaSaida);
        elPresentes.textContent = resumo.pessoasPresentes ?? 0;

    } catch (e) {
        console.error("Erro resumo:", e);
    }
}

// ---------------- INIT ----------------

window.addEventListener("load", async () => {

    const inputData    = document.getElementById("dataInput");
    const inputHoraIni = document.getElementById("horaInicio");
    const inputHoraFim = document.getElementById("horaFim");

    const hoje = new Date().toLocaleDateString('en-CA');

    if (inputData) inputData.value = hoje;
    if (inputHoraIni) inputHoraIni.value = "00";
    if (inputHoraFim) inputHoraFim.value = "23";

    const atualizar = async () => {
        const data = inputData?.value;
        const hIni = inputHoraIni?.value || "00";
        const hFim = inputHoraFim?.value || "23";

        await carregarGrafico(data, hIni, hFim);
        await carregarResumo(data, hIni, hFim);
    };

    await atualizar();

    inputData?.addEventListener("change", atualizar);
    inputHoraIni?.addEventListener("change", atualizar);
    inputHoraFim?.addEventListener("change", atualizar);

    setInterval(atualizar, 5000);
});