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
            .csrf(csrf -> csrf.disable())

            .authorizeHttpRequests(auth -> auth
                .requestMatchers(
                        "/login",
                        // BUG CORRIGIDO: faltava liberar o endpoint de POST do login manual
                        "/processar-login",
                        // BUG CORRIGIDO: faltava liberar registro de usuário
                        "/auth/register",
                        "/api/auth/login",
                        "/css/**",
                        // BUG CORRIGIDO: pasta era "/js/**" mas os arquivos ficam em "/JS/**"
                        "/JS/**",
                        "/img/**",
                        "/images/**",
                        "/webjars/**",
                        "/**/*.css",
                        "/**/*.js"
                ).permitAll()

                .requestMatchers("/api/relatorio/**").hasRole("ADMIN")
                .requestMatchers("/api/dashboard/**").authenticated()

                .anyRequest().authenticated()
            )

            // BUG CORRIGIDO: o formLogin do Spring estava interceptando POST /login e
            // conflitando com o LoginController manual. Como o login é feito manualmente
            // pelo LoginController via /processar-login, desabilitamos o formLogin padrão.
            .formLogin(form -> form.disable())

            .logout(logout -> logout
                .logoutSuccessUrl("/login?logout=true")
                .permitAll()
            )

            .sessionManagement(session -> session
                .sessionCreationPolicy(SessionCreationPolicy.IF_REQUIRED)
            )

            .addFilterBefore(jwtAuthFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}