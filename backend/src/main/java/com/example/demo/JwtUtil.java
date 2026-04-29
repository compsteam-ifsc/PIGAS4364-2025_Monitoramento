    package com.example.demo;

    import io.jsonwebtoken.*;
    import io.jsonwebtoken.security.Keys;
    import org.springframework.beans.factory.annotation.Value;
    import org.springframework.stereotype.Component;

    import javax.crypto.SecretKey;
    import java.nio.charset.StandardCharsets;
    import java.util.Date;

    /**
     * Utilitário JWT: gera e valida tokens para acesso à API pelo Python (YOLO).
     *
     * Configurar em application.properties:
     *   jwt.secret=MinhaChaveSecretaSuperSecura256BitsAqui!!
     *   jwt.expiration-ms=86400000   # 24 horas
     */
    @Component
    public class JwtUtil {

        private final SecretKey secretKey;
        private final long expirationMs;

        public JwtUtil(
            @Value("${jwt.secret}") String secret,
            @Value("${jwt.expiration-ms:86400000}") long expirationMs
        ) {
            // JJWT 0.12+ exige chave com >= 256 bits para HS256
            this.secretKey   = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
            this.expirationMs = expirationMs;
        }

        /** Gera um JWT com username e role como claims. */
        public String generateToken(String username, String role) {
            return Jwts.builder()
                    .subject(username)
                    .claim("role", role)
                    .issuedAt(new Date())
                    .expiration(new Date(System.currentTimeMillis() + expirationMs))
                    .signWith(secretKey)
                    .compact();
        }

        /** Extrai o username (subject) do token. */
        public String extractUsername(String token) {
            return parseClaims(token).getSubject();
        }

        /** Extrai a role do token. */
        public String extractRole(String token) {
            return (String) parseClaims(token).get("role");
        }

        /** Valida assinatura e expiração. */
        public boolean isValid(String token) {
            try {
                parseClaims(token);
                return true;
            } catch (JwtException | IllegalArgumentException e) {
                return false;
            }
        }

        // --- privado ---

        private Claims parseClaims(String token) {
            return Jwts.parser()
                    .verifyWith(secretKey)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        }
    }
