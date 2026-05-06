package com.example.demo.Controllers;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
@Controller
public class PaginaInicialController {
    @GetMapping("/Pagina-Inicial")
    public String PaginaInical(){
        return "Pagina-Inicial";
    }
      
}
