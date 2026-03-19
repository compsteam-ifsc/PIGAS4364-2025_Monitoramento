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
    private PasswordEncoder passwordEncoder;

 public boolean login(String usuario, String senhaDigitada) {
        conexaoUsuario user = repo.findByUsuario(usuario);

        if (user == null) {
            return false;
        }

         return passwordEncoder.matches(senhaDigitada, user.getSenha());
    }
public conexaoUsuario cadastrar(String usuario, String senha) {
        conexaoUsuario novo = new conexaoUsuario();

        novo.setUsuario(usuario);
        novo.setSenha(passwordEncoder.encode(senha));

        return repo.save(novo);
    }



        
    }