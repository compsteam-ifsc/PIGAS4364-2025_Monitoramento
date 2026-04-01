package com.example.demo.Controllers;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

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
        LocalDateTime fim = dataLocal.atTime(LocalTime.MAX);

        return repository.fluxoPorHoraFiltrado(inicio, fim);
    }
}