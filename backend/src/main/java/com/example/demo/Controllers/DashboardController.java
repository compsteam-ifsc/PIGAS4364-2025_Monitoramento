package com.example.demo.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import com.example.demo.Repository.horarioRepository;
import com.example.demo.ConexaoDb.Cndb;
import com.example.demo.ConexaoDb.SaidaOuEntrada;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    @Autowired
    private horarioRepository horarioRepo;

    // Formato final que o JS espera: "HH:mm"
    private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("HH:mm");

    @GetMapping("/resumo")
    public Map<String, Object> resumo(
        @RequestParam String inicio,
        @RequestParam String fim
    ) {
        LocalDateTime ini = LocalDateTime.parse(inicio);
        LocalDateTime f   = LocalDateTime.parse(fim);

        Long totalEntradas = horarioRepo.contarEntradasNoDia(ini, f, SaidaOuEntrada.ENTRADA);
        Long totalSaidas   = horarioRepo.contarEntradasNoDia(ini, f, SaidaOuEntrada.SAIDA);

        LocalDateTime primeiraEntrada = horarioRepo.buscarPrimeiraEntrada(ini, f, SaidaOuEntrada.ENTRADA);
        LocalDateTime ultimaSaida     = horarioRepo.buscarUltimaSaida(ini, f, SaidaOuEntrada.SAIDA);

        long entradas = totalEntradas != null ? totalEntradas : 0L;
        long saidas   = totalSaidas   != null ? totalSaidas   : 0L;
        long presentes = Math.max(0, entradas - saidas);

        Map<String, Object> response = new HashMap<>();
        response.put("totalEntradas",   entradas);
        response.put("totalSaidas",     saidas);
        response.put("pessoasPresentes", presentes);
        // Retorna "HH:mm" ou null — o JS trata null como "--:--"
        response.put("primeiraEntrada", primeiraEntrada != null ? primeiraEntrada.format(FORMATTER) : null);
        response.put("ultimaSaida",     ultimaSaida     != null ? ultimaSaida.format(FORMATTER)     : null);

        return response;
    }

    @GetMapping("/fluxo")
    public List<Object[]> fluxoPorHora() {
        return horarioRepo.fluxoPorHora();
    }

    @GetMapping("/filtrado")
    public List<Cndb> buscarPorData(
            @RequestParam("data")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate data,
            @RequestParam(value = "horaInicio", defaultValue = "00") String horaInicio,
            @RequestParam(value = "horaFim",    defaultValue = "23") String horaFim
    ) {
        int hIni = Integer.parseInt(horaInicio);
        int hFim = Integer.parseInt(horaFim);

        LocalDateTime inicio = data.atTime(hIni, 0, 0);
        LocalDateTime fim    = data.atTime(hFim, 59, 59);

        return horarioRepo.findByDiaHorarioBetween(inicio, fim);
    }
}