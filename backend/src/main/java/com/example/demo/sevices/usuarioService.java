package com.example.demo.sevices;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.example.demo.ConexaoDb.conexaoUsuario;
import com.example.demo.Repository.usuarioRepository;

@Service
public class usuarioService {

    @Autowired
    private usuarioRepository repo;

    @Autowired
    private PasswordEncoder encoder;

    public String register(String user, String pass) {
        System.out.print("3 Sdsadsadas");
        if (repo.findByUsuario(user) != null) {
            return "existe";
        }

        conexaoUsuario u = new conexaoUsuario();
        u.setUsuario(user);
        u.setSenha(encoder.encode(pass));
System.out.print("4Sdsadsadas");
        repo.save(u);
        return "OK";
    }
}