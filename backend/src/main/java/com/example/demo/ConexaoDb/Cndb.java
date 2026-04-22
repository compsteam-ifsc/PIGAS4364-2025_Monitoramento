package com.example.demo.ConexaoDb;

import com.fasterxml.jackson.annotation.JsonFormat;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "horario")
public class Cndb {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // Serializa como "2025-04-22T10:30:00" em vez de array [2025,4,22,10,30,0]
    @JsonFormat(shape = JsonFormat.Shape.STRING, pattern = "yyyy-MM-dd'T'HH:mm:ss")
    @Column(name = "dia_horario", nullable = false)
    private LocalDateTime diaHorario;

    @Enumerated(EnumType.STRING)
    @Column(name = "saida_entrada", nullable = false)
    private SaidaOuEntrada saidaEntrada;

    public Cndb() {}

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