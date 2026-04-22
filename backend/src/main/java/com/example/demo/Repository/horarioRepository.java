package com.example.demo.Repository;

import com.example.demo.ConexaoDb.Cndb;
import com.example.demo.ConexaoDb.SaidaOuEntrada;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.time.LocalDateTime;
import java.util.List;

public interface horarioRepository extends JpaRepository<Cndb, Long> {

    @Query("""
        SELECT FUNCTION('HOUR', c.diaHorario), COUNT(c)
        FROM Cndb c
        GROUP BY FUNCTION('HOUR', c.diaHorario)
        ORDER BY FUNCTION('HOUR', c.diaHorario)
    """)
    List<Object[]> fluxoPorHora();

    @Query("""
        SELECT COUNT(c)
        FROM Cndb c
        WHERE c.saidaEntrada = :tipo
        AND c.diaHorario BETWEEN :inicio AND :fim
    """)
    Long contarEntradasNoDia(
        @Param("inicio") LocalDateTime inicio,
        @Param("fim") LocalDateTime fim,
        @Param("tipo") SaidaOuEntrada tipo
    );

    @Query("""
        SELECT MIN(c.diaHorario)
        FROM Cndb c
        WHERE c.saidaEntrada = :tipo
        AND c.diaHorario BETWEEN :inicio AND :fim
    """)
    LocalDateTime buscarPrimeiraEntrada(
        @Param("inicio") LocalDateTime inicio,
        @Param("fim") LocalDateTime fim,
        @Param("tipo") SaidaOuEntrada tipo
    );

    @Query("""
        SELECT MAX(c.diaHorario)
        FROM Cndb c
        WHERE c.saidaEntrada = :tipo
        AND c.diaHorario BETWEEN :inicio AND :fim
    """)
    LocalDateTime buscarUltimaSaida(
        @Param("inicio") LocalDateTime inicio,
        @Param("fim") LocalDateTime fim,
        @Param("tipo") SaidaOuEntrada tipo
    );

    List<Cndb> findByDiaHorarioBetween(LocalDateTime inicio, LocalDateTime fim);
}