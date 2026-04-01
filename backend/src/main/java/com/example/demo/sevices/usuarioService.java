package com.example.demo.sevices;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
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
       
        if (repo.findByUsuario(user) != null) {
            return "existe";
        }
        conexaoUsuario u = new conexaoUsuario();
        u.setUsuario(user);
        u.setSenha(encoder.encode(pass));
        repo.save(u);
        return "OK";
    }
    public UserDetails login(String user, String pass) throws UsernameNotFoundException {
        conexaoUsuario userEntity = repo.findByUsuario(user);
        return User.builder().username(userEntity.getUsuario())
        .password(userEntity.getSenha()).roles("USER").build();
}
}
