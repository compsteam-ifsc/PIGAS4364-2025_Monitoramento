// Mapa de rotas por tipo de relatório
const rotas = {
  diario:  '/Grafico/Diario',
  semanal: '/Grafico/Semanal',
  geral:   '/Grafico/Geral',
};

/**
 * Redireciona para a página do relatório correspondente.
 * @param {'diario' | 'semanal' | 'geral'} tipo
 */
function irPara(tipo) {
  const url = rotas[tipo];

  if (!url) {
    console.error('Tipo de relatório inválido:', tipo);
    return;
  }

  window.location.href = url;
}