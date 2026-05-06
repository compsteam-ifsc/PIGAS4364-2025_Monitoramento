let graficoLinha = null;


function alternarRelatorio() {
    window.location.href = "/Pagina-Inicial";
}

function getAuthHeaders() {
    const token = localStorage.getItem("token");
    return token ? { "Authorization": "Bearer " + token } : {};
}

function nomeDia(dateStr) {
    const dias = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"];
    const d = new Date(dateStr + "T12:00:00");
    return dias[d.getDay()];
}

function formatarData(dateStr) {
    const partes = dateStr.split("-");
    return `${partes[2]}/${partes[1]}`;
}

// ---------------- SEMANA ----------------

function calcularSemana(dataSelecionada) {
    const fim = new Date(dataSelecionada + "T12:00:00");

    const inicio = new Date(fim);
    inicio.setDate(inicio.getDate() - 6);

    return {
        inicio: inicio.toLocaleDateString("en-CA"),
        fim: fim.toLocaleDateString("en-CA")
    };
}

// 🔥 LABEL BONITA DA SEMANA
function atualizarLabelSemana(inicio, fim) {
    const el = document.getElementById("semanaLabel");
    if (!el) return;

    el.textContent = `Semana: ${formatarData(inicio)} → ${formatarData(fim)}`;
}

// ---------------- AGRUPAMENTO ----------------

function montarSemana(dados, inicio, fim) {

    const mapa = {};

    dados.forEach(row => {
        const data = row[1].split("T")[0];
        mapa[data] = (mapa[data] || 0) + Number(row[2]);
    });

    const labels = [];
    const valores = [];

    let cur = new Date(inicio + "T12:00:00");
    const end = new Date(fim + "T12:00:00");

    while (cur <= end) {
        const key = cur.toLocaleDateString("en-CA");

        labels.push(nomeDia(key) + " " + formatarData(key));
        valores.push(mapa[key] || 0); // garante zero

        cur.setDate(cur.getDate() + 1);
    }

    return { labels, valores };
}

// ---------------- GRÁFICO ----------------

async function carregarGraficoLinha(inicio, fim) {

    const res = await fetch(`/api/dashboard/semanal/porDia?inicio=${inicio}T00:00:00&fim=${fim}T23:59:59`, {
        headers: getAuthHeaders()
    });

    if (!res.ok) return;

    const dados = await res.json();

    const { labels, valores } = montarSemana(dados, inicio, fim);

    const ctx = document.getElementById("lineChart")?.getContext("2d");
    if (!ctx) return;

    if (graficoLinha) {
        graficoLinha.data.labels = labels;
        graficoLinha.data.datasets[0].data = valores;
        graficoLinha.update();
        return;
    }

    graficoLinha = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Movimentação",
                data: valores,
                borderColor: "rgba(37,99,235,0.9)",
                backgroundColor: "rgba(37,99,235,0.1)",
                fill: true,
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });
}

// ---------------- RESUMO ----------------

async function carregarResumoSemanal(inicio, fim) {

    const res = await fetch(`/api/dashboard/semanal/resumo?inicio=${inicio}T00:00:00&fim=${fim}T23:59:59`, {
        headers: getAuthHeaders()
    });

    if (!res.ok) return;

    const r = await res.json();

    document.getElementById("totalEntradas").textContent = r.totalEntradas ?? "--";
    document.getElementById("totalSaidas").textContent = r.totalSaidas ?? "--";
}

// ---------------- INIT ----------------

window.addEventListener("load", async () => {

    const input = document.getElementById("dataInput");
    const hoje = new Date().toLocaleDateString("en-CA");

    if (input) input.value = hoje;

    const atualizar = async () => {
        const data = input?.value;
        if (!data) return;

        const { inicio, fim } = calcularSemana(data);

        atualizarLabelSemana(inicio, fim);

        await carregarGraficoLinha(inicio, fim);
        await carregarResumoSemanal(inicio, fim);
    };

    await atualizar();

    input?.addEventListener("change", atualizar);

    setInterval(atualizar, 30000);
});