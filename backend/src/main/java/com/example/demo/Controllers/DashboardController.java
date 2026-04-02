package com.example.demo.Controllers;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.demo.Repository.FiltroRepository;
import com.example.demo.Repository.horarioRepository;

@RestController
@RequestMapping("/dashboard")
public class DashboardController {

    @Autowired
    private FiltroRepository repository;

    @Autowired
    private horarioRepository horarioRepo;

    @GetMapping("/dados")
    public List<Object[]> fluxoHora() {
        return horarioRepo.fluxoPorHora();
    }

    @GetMapping("/filtrado")
    public List<Object[]> fluxoFiltrado(@RequestParam String data) {
        LocalDate dataLocal = LocalDate.parse(data);
        LocalDateTime inicio = dataLocal.atStartOfDay();
        LocalDateTime fim = dataLocal.atTime(23, 59, 59);

        return repository.fluxoPorHoraFiltrado(inicio, fim);
    }

    @GetMapping("/resumo")
    public Map<String, Object> resumoDia(@RequestParam String data) {
        LocalDate dataLocal = LocalDate.parse(data);
        LocalDateTime inicio = dataLocal.atStartOfDay();
        LocalDateTime fim = dataLocal.atTime(23, 59, 59);

        Long totalEntradas = horarioRepo.contarEntradasNoDia(inicio, fim);
        LocalDateTime primeiraEntrada = horarioRepo.buscarPrimeiraEntrada(inicio, fim);
        LocalDateTime ultimaSaida = horarioRepo.buscarUltimaSaida(inicio, fim);

        Map<String, Object> resumo = new HashMap<>();
        resumo.put("totalEntradas", totalEntradas != null ? totalEntradas : 0);
        resumo.put("primeiraEntrada", formatarHora(primeiraEntrada));
        resumo.put("ultimaSaida", formatarHora(ultimaSaida));

        return resumo;
    }

    private String formatarHora(LocalDateTime dataHora) {
        if (dataHora == null) {
            return "--:--";
        }

        return dataHora.toLocalTime().format(DateTimeFormatter.ofPattern("HH:mm"));
    }
}