package com.example.demo.Controllers;

import org.slf4j.Logger;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContext;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.context.HttpSessionSecurityContextRepository;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

import com.example.demo.sevices.usuarioService;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;

@Controller
public class LoginController {

    
    @Autowired
    private PasswordEncoder encoder;

    @Autowired
private usuarioService us;

    @GetMapping("/login")
    public String mostrarLogin() {
        return "cadastroLogin";
    }

     @PostMapping("/processar-login")
    public String autenticar(@RequestParam String user, @RequestParam String pass, RedirectAttributes redirectAttributes, HttpServletRequest request ) {
       try {
            UserDetails userDetails = us.login(user, pass);

            // verifica se encontrou usuário e se a senha bate
            if (userDetails != null && encoder.matches(pass, userDetails.getPassword())) {

                // 1) Cria o objeto Authentication
                UsernamePasswordAuthenticationToken authToken =
                        new UsernamePasswordAuthenticationToken(
                                userDetails,
                                null,
                                userDetails.getAuthorities()
                        );

                // 2) Cria e seta no SecurityContext
                SecurityContext context = SecurityContextHolder.createEmptyContext();
                context.setAuthentication(authToken);
                SecurityContextHolder.setContext(context);

                // 3) Salva na sessão HTTP (importantíssimo!)
                HttpSession session = request.getSession(true);
                session.setAttribute(
                        HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY,
                        context
                );

                redirectAttributes.addFlashAttribute("message", "Login realizado com sucesso");
                redirectAttributes.addFlashAttribute("alertClass", "alert-success");

                return "redirect:/Grafico";
            }

            redirectAttributes.addFlashAttribute("message", "Usuário ou senha inválidos");
            redirectAttributes.addFlashAttribute("alertClass", "alert-danger");
            return "redirect:/login";

        } catch (Exception e) {
            e.printStackTrace();
            redirectAttributes.addFlashAttribute("message", "Erro ao realizar login");
            redirectAttributes.addFlashAttribute("alertClass", "alert-danger");
            return "redirect:/login";
        }
    }
}