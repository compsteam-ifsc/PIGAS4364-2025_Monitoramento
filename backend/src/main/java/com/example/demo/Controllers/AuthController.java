package com.example.demo.Controllers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import com.example.demo.sevices.usuarioService;

@RestController
@RequestMapping("/auth")
@CrossOrigin(origins = "*")
public class AuthController {

    @Autowired
    private usuarioService service;

    @PostMapping("/register")
    public String register(@RequestBody UsuarioDTO dto) {
        return service.register(dto.getUser(), dto.getPass());
    }
    @PostMapping("/login")
public String login(@RequestBody UsuarioDTO dto) {
    return service.login(dto.getUser(), dto.getPass());
}
}