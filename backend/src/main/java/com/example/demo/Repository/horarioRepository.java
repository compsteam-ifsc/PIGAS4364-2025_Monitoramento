package com.example.demo.Repository;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import com.example.demo.ConexaoDb.Cndb;

public interface horarioRepository extends JpaRepository<Cndb, Long> {

    @Query("""
        SELECT HOUR(c.diaHorario), COUNT(c)
        FROM Cndb c
        GROUP BY HOUR(c.diaHorario)
        ORDER BY HOUR(c.diaHorario)
    """)
    List<Object[]> fluxoPorHora();

    @Query("""
        SELECT COUNT(c)
        FROM Cndb c
        WHERE c.saidaEntrada = com.example.demo.ConexaoDb.SaidaOuEntrada.ENTRADA
        AND c.diaHorario BETWEEN :inicio AND :fim
    """)
    Long contarEntradasNoDia(LocalDateTime inicio, LocalDateTime fim);

    @Query("""
        SELECT MIN(c.diaHorario)
        FROM Cndb c
        WHERE c.saidaEntrada = com.example.demo.ConexaoDb.SaidaOuEntrada.ENTRADA
        AND c.diaHorario BETWEEN :inicio AND :fim
    """)
    LocalDateTime buscarPrimeiraEntrada(LocalDateTime inicio, LocalDateTime fim);

    @Query("""
        SELECT MAX(c.diaHorario)
        FROM Cndb c
        WHERE c.saidaEntrada = com.example.demo.ConexaoDb.SaidaOuEntrada.SAIDA
        AND c.diaHorario BETWEEN :inicio AND :fim
    """)
    LocalDateTime buscarUltimaSaida(LocalDateTime inicio, LocalDateTime fim);
}