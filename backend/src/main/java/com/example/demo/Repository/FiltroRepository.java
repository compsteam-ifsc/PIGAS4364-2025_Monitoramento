package com.example.demo.Repository;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.example.demo.ConexaoDb.Cndb;

public interface FiltroRepository extends JpaRepository<Cndb, Integer> {

    @Query("""
        SELECT HOUR(c.diaHorario), COUNT(c)
        FROM Cndb c
        WHERE c.diaHorario BETWEEN :inicio AND :fim
        GROUP BY HOUR(c.diaHorario)
        ORDER BY HOUR(c.diaHorario)
    """)
    List<Object[]> fluxoPorHoraFiltrado(LocalDateTime inicio, LocalDateTime fim);
}