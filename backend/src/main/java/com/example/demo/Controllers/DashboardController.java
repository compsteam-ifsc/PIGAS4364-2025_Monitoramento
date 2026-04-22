package com.example.demo.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.web.bind.annotation.*;

import com.example.demo.Repository.horarioRepository;
import com.example.demo.ConexaoDb.Cndb;
import com.example.demo.ConexaoDb.SaidaOuEntrada;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/dashboard")
public class DashboardController {

    @Autowired
    private horarioRepository horarioRepo;

    // ================= RESUMO =================
    @GetMapping("/resumo")
    public Map<String, Object> resumo(
        @RequestParam String inicio,
        @RequestParam String fim
    ) {

        LocalDateTime ini = LocalDateTime.parse(inicio);
        LocalDateTime f = LocalDateTime.parse(fim);

        Long totalEntradas = horarioRepo.contarEntradasNoDia(
            ini, f, SaidaOuEntrada.ENTRADA
        );

        LocalDateTime primeiraEntrada = horarioRepo.buscarPrimeiraEntrada(
            ini, f, SaidaOuEntrada.ENTRADA
        );

        LocalDateTime ultimaSaida = horarioRepo.buscarUltimaSaida(
            ini, f, SaidaOuEntrada.SAIDA
        );

        Map<String, Object> response = new HashMap<>();
        response.put("totalEntradas", totalEntradas);
        response.put("primeiraEntrada", primeiraEntrada);
        response.put("ultimaSaida", ultimaSaida);

        return response;
    }

    // ================= FLUXO =================
    @GetMapping("/fluxo")
    public List<Object[]> fluxoPorHora() {
        return horarioRepo.fluxoPorHora();
    }

    @GetMapping("/filtrado")
    public List<Cndb> buscarPorData(
            @RequestParam("data")
            @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
            LocalDate data
    ) {

        LocalDateTime inicio = data.atStartOfDay();
        LocalDateTime fim = data.atTime(23, 59, 59);

        return horarioRepo.findByDiaHorarioBetween(inicio, fim);
    }
}