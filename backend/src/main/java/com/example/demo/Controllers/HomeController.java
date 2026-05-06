package com.example.demo.Controllers;

import java.security.Principal;

import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class HomeController {

    @GetMapping("/Grafico/Diario")
    public String home(Model model, Principal principal) {
        String nomeUsuario = (principal != null) ? principal.getName() : "Usuário";
        model.addAttribute("nomeUsuario", nomeUsuario);

        return "relatorioDiario";
    }
     @GetMapping("Grafico/Semanal")
    public String semanal(Model model, Principal principal) {
        String nomeUsuario = (principal != null) ? principal.getName() : "Usuário";
        model.addAttribute("nomeUsuario", nomeUsuario);

        return "relatorioSemanal";
    }
    @GetMapping("Grafico/Geral")
        public String geral(Model model, Principal principal) {
            String nomeUsuario = (principal != null) ? principal.getName() : "Usuário";
            model.addAttribute("nomeUsuario", nomeUsuario);

        return "relatorioGeral";
    }





}