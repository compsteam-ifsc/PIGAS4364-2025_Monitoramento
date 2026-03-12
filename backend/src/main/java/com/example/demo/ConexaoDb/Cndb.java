package com.example.demo.ConexaoDb;

import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.Id;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Table;

import java.time.LocalDateTime;

import jakarta.persistence.Column;



@Entity
@Table(name = "horario")
public class Cndb {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "dia_horario")
    private LocalDateTime diaHorario;

    @Enumerated(EnumType.STRING)
private SaidaOuEntrada saida;
    
}