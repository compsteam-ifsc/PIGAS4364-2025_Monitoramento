package com.example.demo.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.example.demo.model.Usuario;
import com.example.demo.Repository.UsuarioRepository;

@Service
public class UsuarioService {

    @Autowired
    private UsuarioRepository repo;

    @Autowired
    private PasswordEncoder encoder;

    public String register(String user, String pass) {
        if (repo.findByUser(user) != null) {
            return "Usuário já existe";
        }

        Usuario u = new Usuario();
        u.setUser(user);
        u.setPass(encoder.encode(pass));

        repo.save(u);
        return "Registrado com sucesso";
    }

    public String login(String user, String pass) {
        Usuario u = repo.findByUser(user);

        if (u == null) return "Usuário não encontrado";

        if (encoder.matches(pass, u.getPass())) {
            return "Login OK";
        }

        return "Senha inválida";
    }
}