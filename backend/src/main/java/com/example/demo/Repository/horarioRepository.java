package com.example.demo.Repository;
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
}




