package com.example.demo.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import com.example.demo.Repository.daterRepository;
import com.example.demo.ConexaoDb.Cndb;
import java.time.LocalDateTime;
import java.util.List;

@RestController
@RequestMapping("/api")
public class RelatorioController {

    @Autowired
    private daterRepository repo;

    @PostMapping("/relatorio")
    public String salvar(@RequestBody Cndb dto) {

        Cndb registro = new Cndb();
        registro.setDiaHorario(LocalDateTime.now());
        registro.setSaidaEntrada(dto.getSaidaEntrada());

        repo.save(registro);

        return "Salvo com sucesso";
    }
    @GetMapping("/relatorio")
  public List<Cndb> listar() {
    return repo.findAll();
}
}