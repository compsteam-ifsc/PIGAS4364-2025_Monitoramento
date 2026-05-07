package com.example.demo.Controllers;

import jakarta.servlet.RequestDispatcher;
import jakarta.servlet.http.HttpServletRequest;

import org.springframework.boot.webmvc.error.ErrorController;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.RequestMapping;

@Controller
public class CustomErrorController implements ErrorController {

    @RequestMapping("/error")
    public String handleError(HttpServletRequest request) {
        Object status = request.getAttribute(RequestDispatcher.ERROR_STATUS_CODE);

        if (status != null) {
            Integer statusCode = Integer.valueOf(status.toString());

            // Se for erro 404 (Não Encontrado)
            if (statusCode == HttpStatus.NOT_FOUND.value()) {
                // Redireciona para a sua página inicial após o login
                return "redirect:/Pagina-Inicial"; 
            }
        }
        
        // Se for outro erro (ex: 500), você pode mandar para uma página de erro genérica
        return "error"; 
    }
}