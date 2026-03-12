package com.example.demo.ConexaoDb;
    import java.time.LocalDateTime;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
    import jakarta.persistence.GenerationType;
        import jakarta.persistence.Id;
        import jakarta.persistence.Table;

    @Entity
    @Table(name = "horario")
public class Cndb { 
 @Id
   @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "dia_horario", nullable = false)
    private LocalDateTime dia_horario;

        @Enumerated(EnumType.STRING)
    @Column(name = "Saida_chegada", length = 1, nullable = false)
      private SaidaOuEntrada saidaChegada;
   


    
}


