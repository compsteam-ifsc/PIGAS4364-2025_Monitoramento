package com.example.demo.ConexaoDb;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "horario")
public class Cndb {
   
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "dia_horario")
    private LocalDateTime diaHorario;

    @Enumerated(EnumType.STRING)
    @Column(name = "saida_entrada") 
    private SaidaOuEntrada saidaEntrada;

    public Long getId() { 
        return id; 
    }

    public LocalDateTime getDiaHorario() { 
        return diaHorario; 
    }

    public void setDiaHorario(LocalDateTime diaHorario) {
        this.diaHorario = diaHorario;
    }

    public SaidaOuEntrada getSaidaEntrada() {
        return saidaEntrada;
    }

    public void setSaidaEntrada(SaidaOuEntrada saidaEntrada) {
        this.saidaEntrada = saidaEntrada;
    }
}