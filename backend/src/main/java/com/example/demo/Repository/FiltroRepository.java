package com.example.demo.Repository;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.example.demo.ConexaoDb.Cndb;
import com.example.demo.ConexaoDb.SaidaOuEntrada;

@Repository
public interface FiltroRepository extends JpaRepository<Cndb, Integer> {
    
    // Busca registros entre duas datas/horas específicas
    List<Cndb> findByDiaHorarioBetween(LocalDateTime inicio, LocalDateTime fim);
    List<Cndb> findBySaida(SaidaOuEntrada saida);
}
