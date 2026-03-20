package com.example.demo.Controllers;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class usuarioController {
    @GetMapping("/login")
    public String usuario(){
        return "cadastroLogin";
    }
}
