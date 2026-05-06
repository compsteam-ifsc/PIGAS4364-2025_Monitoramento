let graficoLinha = null;

// ---------------- BOTÃO ----------------

function alternarRelatorio() {
    window.location.href = "/Pagina-Inicial";
}

// ---------------- UTIL ----------------

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

// ---------------- RANGE ----------------

function obterRange() {
    let inicio = document.getElementById("dataInicio")?.value;
    let fim = document.getElementById("dataFim")?.value;

    if (!inicio || !fim) return null;

    if (inicio > fim) {
        [inicio, fim] = [fim, inicio];
    }

    return { inicio, fim };
}

// ---------------- AGRUPAMENTO ----------------

function agruparDados(dados, inicio, fim) {

    const mapa = {};

    dados.forEach(row => {
        const data = row[1].split("T")[0];
        const qtd = Number(row[2]);
        mapa[data] = (mapa[data] || 0) + qtd;
    });

    const diasTotal = (new Date(fim) - new Date(inicio)) / (1000 * 60 * 60 * 24);

    const labels = [];
    const valores = [];

    // ----------- ATÉ 30 DIAS (por dia) -----------
    if (diasTotal <= 30) {

        const cur = new Date(inicio + "T12:00:00");
        const end = new Date(fim + "T12:00:00");

        while (cur <= end) {
            const key = cur.toLocaleDateString("en-CA");

            labels.push(nomeDia(key) + " " + formatarData(key));
            valores.push(mapa[key] || 0);

            cur.setDate(cur.getDate() + 1);
        }
    }

    // ----------- ATÉ 120 DIAS (por semana) -----------
    else if (diasTotal <= 120) {

        let cur = new Date(inicio + "T12:00:00");
        const end = new Date(fim + "T12:00:00");

        while (cur <= end) {

            let soma = 0;
            let inicioSemana = cur.toLocaleDateString("en-CA");

            for (let i = 0; i < 7 && cur <= end; i++) {
                const key = cur.toLocaleDateString("en-CA");
                soma += mapa[key] || 0;
                cur.setDate(cur.getDate() + 1);
            }

            let fimSemana = new Date(cur);
            fimSemana.setDate(fimSemana.getDate() - 1);

            const fimStr = fimSemana.toLocaleDateString("en-CA");

            labels.push(`${formatarData(inicioSemana)} - ${formatarData(fimStr)}`);
            valores.push(soma);
        }
    }

    // ----------- MAIS DE 120 DIAS (por mês) -----------
    else {

        const mapaMes = {};

        // soma valores existentes
        Object.keys(mapa).forEach(data => {
            const mes = data.substring(0, 7);
            mapaMes[mes] = (mapaMes[mes] || 0) + mapa[data];
        });

        const nomesMes = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];

        let cur = new Date(inicio + "T12:00:00");
        const end = new Date(fim + "T12:00:00");

        cur.setDate(1);

        while (cur <= end) {

            const ano = cur.getFullYear();
            const mesNum = cur.getMonth() + 1;

            const mesKey = `${ano}-${String(mesNum).padStart(2, "0")}`;

            labels.push(nomesMes[mesNum - 1] + "/" + ano);
            valores.push(mapaMes[mesKey] || 0);

            cur.setMonth(cur.getMonth() + 1);
        }
    }

    return { labels, valores };
}

// ---------------- GRÁFICO ----------------

async function carregarGraficoLinha(inicio, fim) {

    try {
        const res = await fetch(`/api/dashboard/geral/porDia?inicio=${inicio}T00:00:00&fim=${fim}T23:59:59`, {
            headers: getAuthHeaders()
        });

        if (!res.ok) {
            console.error("Erro API gráfico:", res.status);
            return;
        }

        const dados = await res.json();

        const { labels, valores } = agruparDados(dados, inicio, fim);

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
                    tension: 0.4,
                    pointRadius: 3,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false, // 🔥 ESSENCIAL

                plugins: {
                    legend: { display: false }
                },

                scales: {
                    x: {
                        grid: { display: false }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0 }
                    }
                }
            }
        });

    } catch (e) {
        console.error("Erro gráfico:", e);
    }
}

// ---------------- RESUMO ----------------

async function carregarResumoGeral(inicio, fim) {

    try {
        const res = await fetch(`/api/dashboard/geral/resumo?inicio=${inicio}T00:00:00&fim=${fim}T23:59:59`, {
            headers: getAuthHeaders()
        });

        if (!res.ok) return;

        const r = await res.json();

        document.getElementById("totalEntradas").textContent = r.totalEntradas ?? "--";
        document.getElementById("totalSaidas").textContent = r.totalSaidas ?? "--";

        const res2 = await fetch(`/api/dashboard/geral/porDia?inicio=${inicio}T00:00:00&fim=${fim}T23:59:59`, {
            headers: getAuthHeaders()
        });

        const dados = await res2.json();

        const mapa = {};

        dados.forEach(row => {
            const d = row[1].split("T")[0];
            mapa[d] = (mapa[d] || 0) + Number(row[2]);
        });

        const keys = Object.keys(mapa);

        if (keys.length > 0) {
            const pico = keys.reduce((a, b) => mapa[a] >= mapa[b] ? a : b);

            document.getElementById("diaPico").textContent =
                nomeDia(pico) + " " + formatarData(pico);
        } else {
            document.getElementById("diaPico").textContent = "--";
        }

    } catch (e) {
        console.error("Erro resumo:", e);
    }
}

// ---------------- INIT ----------------

window.addEventListener("load", async () => {

    const dataInicio = document.getElementById("dataInicio");
    const dataFim = document.getElementById("dataFim");

    const hoje = new Date().toLocaleDateString("en-CA");

    if (dataInicio) dataInicio.value = hoje;
    if (dataFim) dataFim.value = hoje;

    const atualizar = async () => {

        const range = obterRange();
        if (!range) return;

        const { inicio, fim } = range;

        await carregarGraficoLinha(inicio, fim);
        await carregarResumoGeral(inicio, fim);
    };

    await atualizar();

    dataInicio?.addEventListener("change", atualizar);
    dataFim?.addEventListener("change", atualizar);

    setInterval(atualizar, 30000);
});