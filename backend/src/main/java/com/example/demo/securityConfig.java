package com.example.demo;

import com.example.demo.sevices.CustomUserDetailsService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

@Configuration
public class securityConfig {

    @Autowired
    private JwtAuthFilter jwtAuthFilter;

    @Autowired
    private CustomUserDetailsService userDetailsService;

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {

        http
            // Desabilita CSRF (API/JWT geralmente precisa disso)
            .csrf(csrf -> csrf.disable())

            // Configuração de rotas
            .authorizeHttpRequests(auth -> auth

                // 🔓 ROTAS PÚBLICAS
                .requestMatchers(
                        "/login",
                        "/api/auth/login",

                        // ARQUIVOS ESTÁTICOS
                        "/css/**",
                        "/js/**",
                        "/img/**",
                        "/images/**",
                        "/webjars/**",
                        "/**/*.css",
                        "/**/*.js"
                ).permitAll()

                // 🔒 ROTAS PROTEGIDAS
                .requestMatchers("/api/relatorio/**").hasRole("ADMIN")
                .requestMatchers("/api/dashboard/**").authenticated()

                // 🔐 QUALQUER OUTRA REQUISIÇÃO
                .anyRequest().authenticated()
            )

            // Login com formulário
            .formLogin(form -> form
                .loginPage("/login")
                .defaultSuccessUrl("/Grafico/Diario", true)
                .permitAll()
            )

            // Logout
            .logout(logout -> logout
                .logoutSuccessUrl("/login?logout=true")
                .permitAll()
            )

            // Sessão
            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
            )

            // Filtro JWT antes do padrão
            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}