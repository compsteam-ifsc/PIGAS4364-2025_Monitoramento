    package com.example.demo.Repository;
    import org.springframework.data.jpa.repository.JpaRepository;
    import com.example.demo.ConexaoDb.conexaoUsuario;
    public interface usuarioRepository extends JpaRepository<conexaoUsuario, Long>{
      
        conexaoUsuario findByUsuario(String usuario);
    }




