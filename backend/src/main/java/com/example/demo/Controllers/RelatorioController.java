package com.example.demo.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import com.example.demo.Repository.daterRepository;
import com.example.demo.ConexaoDb.Cndb;
import com.example.demo.ConexaoDb.SaidaOuEntrada;


import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class RelatorioController {

    @Autowired
    private daterRepository repo;

    @PostMapping("/relatorio")
public String salvar(@RequestBody Map<String, String> body) {

    try {
        String tipo = body.get("saidaEntrada");

        System.out.println("Recebido: " + tipo);

        if (tipo == null) {
            return "Erro: campo saidaEntrada é obrigatório";
        }

        SaidaOuEntrada enumValue;

        try {
            enumValue = SaidaOuEntrada.valueOf(tipo.toUpperCase());
        } catch (Exception e) {
            return "Erro: use ENTRADA ou SAIDA";
        }

        Cndb registro = new Cndb();
        registro.setDiaHorario(LocalDateTime.now());
        registro.setSaidaEntrada(enumValue);

        repo.save(registro);

        return "Salvo com sucesso";

    } catch (Exception e) {
        e.printStackTrace();
        return "Erro interno: " + e.getMessage();
    }
}

    
    @GetMapping("/relatorio")
    public List<Map<String, Object>> listar() {
        return repo.findAll().stream().map(c -> {
            Map<String, Object> m = new HashMap<>();
            m.put("id", c.getId());
            m.put("diaHorario", c.getDiaHorario());
            m.put("saidaEntrada", c.getSaidaEntrada());
            return m;
        }).toList();
    }
}