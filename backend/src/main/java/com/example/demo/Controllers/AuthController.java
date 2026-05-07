package com.example.demo.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import com.example.demo.sevices.usuarioService;

@Controller
@RequestMapping("/auth")
@CrossOrigin(origins = "*")
public class AuthController {

    @Autowired
    private usuarioService service;

    @PostMapping("/register")
    public String register(@RequestParam String registerUser,
                           @RequestParam String registerPass,
                           RedirectAttributes redirectAttributes) {

        String retorno = service.register(registerUser, registerPass);

        // BUG CORRIGIDO: comparação de String com == trocada por .equals()
        if ("OK".equals(retorno)) {
            redirectAttributes.addFlashAttribute("message", "Cadastro realizado com sucesso");
            redirectAttributes.addFlashAttribute("alertClass", "alert-success");
            return "redirect:/login";
        } else {
            redirectAttributes.addFlashAttribute("message", "Erro ao cadastrar usuário");
            redirectAttributes.addFlashAttribute("alertClass", "alert-danger");
            return "redirect:/login";
        }
    }
}