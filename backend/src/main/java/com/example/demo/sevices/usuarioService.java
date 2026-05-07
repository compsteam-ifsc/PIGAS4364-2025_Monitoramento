package com.example.demo.sevices;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import com.example.demo.ConexaoDb.conexaoUsuario;
import com.example.demo.Repository.usuarioRepository;

import java.util.List;

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
        u.setRole("ROLE_USER"); // role padrão explícita
        repo.save(u);
        return "OK";
    }

    // BUG CORRIGIDO: antes hardcodava "USER" ignorando a role real do banco
    public UserDetails login(String user, String pass) throws UsernameNotFoundException {
        conexaoUsuario userEntity = repo.findByUsuario(user);

        if (userEntity == null) {
            throw new UsernameNotFoundException("Usuário não encontrado: " + user);
        }

        return new User(
            userEntity.getUsuario(),
            userEntity.getSenha(),
            List.of(new SimpleGrantedAuthority(userEntity.getRole()))
        );
    }
}