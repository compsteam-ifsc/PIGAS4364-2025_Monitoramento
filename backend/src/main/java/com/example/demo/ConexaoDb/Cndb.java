package com.example.demo.ConexaoDb;

import jakarta.persistence.*;
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