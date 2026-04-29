package com.example.demo.sevices;

import com.example.demo.ConexaoDb.conexaoUsuario;
import com.example.demo.Repository.usuarioRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.*;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Carrega o usuário do banco e repassa a role real (ROLE_ADMIN / ROLE_USER)
 * para o Spring Security — necessário tanto para o form login quanto para o JWT.
 */
@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    private usuarioRepository repo;

    @Override
    public UserDetails loadUserByUsername(String username) throws UsernameNotFoundException {
        conexaoUsuario usuario = repo.findByUsuario(username);

        if (usuario == null) {
            throw new UsernameNotFoundException("Usuário não encontrado: " + username);
        }

        // Usa a role salva no banco (não hardcoded "USER")
        return new org.springframework.security.core.userdetails.User(
            usuario.getUsuario(),
            usuario.getSenha(),
            List.of(new SimpleGrantedAuthority(usuario.getRole()))
        );
    }
}
