package com.example.demo.ConexaoDb;

import jakarta.persistence.*;

@Entity
@Table(name = "usuario")
public class conexaoUsuario {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "usuario", unique = true, nullable = false)
    private String usuario;

    @Column(name = "senha", nullable = false)
    private String senha;

    /**
     * Role do usuário: "ROLE_ADMIN" ou "ROLE_USER".
     * Valor padrão no banco deve ser "ROLE_USER".
     * ALTER TABLE usuario ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'ROLE_USER';
     * Para tornar alguém admin: UPDATE usuario SET role = 'ROLE_ADMIN' WHERE usuario = 'seu_admin';
     */
    @Column(name = "role", nullable = false)
    private String role = "ROLE_USER";

    public conexaoUsuario() {}

    public conexaoUsuario(String usuario, String senha) {
        this.usuario = usuario;
        this.senha   = senha;
    }

    // --- getters / setters ---

    public Long getId() { return id; }

    public String getUsuario() { return usuario; }
    public void setUsuario(String usuario) { this.usuario = usuario; }

    public String getSenha() { return senha; }
    public void setSenha(String senha) { this.senha = senha; }

    public String getRole() { return role; }
    public void setRole(String role) { this.role = role; }
}
