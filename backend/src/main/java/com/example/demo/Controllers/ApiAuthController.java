package com.example.demo.Controllers;

import com.example.demo.ConexaoDb.conexaoUsuario;
import com.example.demo.Repository.usuarioRepository;
import com.example.demo.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * Endpoint REST de autenticação para clientes externos (ex: script Python YOLO).
 *
 * POST /api/auth/login
 * Body JSON: { "usuario": "admin", "senha": "123456" }
 * Resposta:  { "token": "<jwt>", "role": "ROLE_ADMIN" }
 *
 * Apenas usuários com ROLE_ADMIN recebem um token válido para
 * acessar rotas protegidas da API.
 */
@RestController
@RequestMapping("/api/auth")
public class ApiAuthController {

    @Autowired
    private usuarioRepository usuarioRepo;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtUtil jwtUtil;

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody Map<String, String> body) {

        String usuario = body.get("usuario");
        String senha   = body.get("senha");

        if (usuario == null || senha == null) {
            return ResponseEntity
                .badRequest()
                .body(Map.of("erro", "Campos 'usuario' e 'senha' são obrigatórios"));
        }

        conexaoUsuario user = usuarioRepo.findByUsuario(usuario);

        if (user == null || !passwordEncoder.matches(senha, user.getSenha())) {
            return ResponseEntity
                .status(HttpStatus.UNAUTHORIZED)
                .body(Map.of("erro", "Credenciais inválidas"));
        }

        // Somente ROLE_ADMIN pode usar a API do Python
        if (!"ROLE_ADMIN".equals(user.getRole())) {
            return ResponseEntity
                .status(HttpStatus.FORBIDDEN)
                .body(Map.of("erro", "Acesso negado: apenas administradores podem usar a API"));
        }

        String token = jwtUtil.generateToken(user.getUsuario(), user.getRole());

        return ResponseEntity.ok(Map.of(
            "token", token,
            "role",  user.getRole()
        ));
    }
}
