package com.example.demo.Controllers;

import java.util.List;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.example.demo.Repository.horarioRepository;

@RestController
@RequestMapping("/dashboard")
public class DashboardController {

 @Autowired
 horarioRepository repository;

 @GetMapping("/dados")
 public List<Object[]> fluxoHora(){
     return repository.fluxoPorHora();
 }

}