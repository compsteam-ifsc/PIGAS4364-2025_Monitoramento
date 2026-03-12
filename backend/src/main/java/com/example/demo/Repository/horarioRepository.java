package com.example.demo.Repository;
import java.util.List;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;


import com.example.demo.ConexaoDb.Cndb;
public interface horarioRepository extends JpaRepository<Cndb, Long> {
  @Query(value = """
    SELECT HOUR(dia_horario), COUNT(dia_horario)
    FROM horario
    WHERE dia_horario <= '2026-03-10 23:59:59'
      AND dia_horario >= '2026-03-10 00:00:00'
    GROUP BY HOUR(dia_horario)
    ORDER BY HOUR(dia_horario) ASC
    """, nativeQuery = true)
    List<Object[]> fluxoPorHora();
}




