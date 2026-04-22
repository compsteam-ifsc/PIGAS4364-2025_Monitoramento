package com.example.demo.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import com.example.demo.Repository.daterRepository;
import com.example.demo.ConexaoDb.Cndb;

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
public String salvar(@RequestBody Cndb dto) {

    try {
        System.out.println("Recebido: " + dto.getSaidaEntrada());

        if (dto.getSaidaEntrada() == null) {
            return "Erro: saidaEntrada veio NULL";
        }

        Cndb registro = new Cndb();
        registro.setDiaHorario(LocalDateTime.now());
        registro.setSaidaEntrada(dto.getSaidaEntrada());

        repo.save(registro);

        return "Salvo com sucesso";

    } catch (Exception e) {
        e.printStackTrace();
        return "Erro: " + e.getMessage();
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