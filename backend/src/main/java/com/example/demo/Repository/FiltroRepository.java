package com.example.demo.Repository;

import com.example.demo.ConexaoDb.Cndb;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface FiltroRepository extends JpaRepository<Cndb, Long> {

    @Query("""
        SELECT FUNCTION('HOUR', c.diaHorario), COUNT(c)
        FROM Cndb c
        WHERE c.diaHorario BETWEEN :inicio AND :fim
        GROUP BY FUNCTION('HOUR', c.diaHorario)
        ORDER BY FUNCTION('HOUR', c.diaHorario)
    """)
    List<Object[]> fluxoPorHoraFiltrado(
        @Param("inicio") LocalDateTime inicio,
        @Param("fim") LocalDateTime fim
    );
}