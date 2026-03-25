package com.example.demo.sevices;

import com.example.demo.ConexaoDb.conexaoUsuario;
import com.example.demo.Repository.usuarioRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.*;
import org.springframework.stereotype.Service;

@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    private usuarioRepository repo;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        conexaoUsuario usuario = repo.findByUsuario(username);

        if (usuario == null) {
            throw new UsernameNotFoundException("Usuário não encontrado");
        }

        return User.builder()
                .username(usuario.getUsuario())
                .password(usuario.getSenha())
                .roles("USER")
                .build();
    }
}