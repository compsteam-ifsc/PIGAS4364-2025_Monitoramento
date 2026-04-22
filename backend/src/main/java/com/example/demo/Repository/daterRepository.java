package com.example.demo.Repository;
import org.springframework.data.jpa.repository.JpaRepository;
import com.example.demo.ConexaoDb.Cndb;
import java.time.LocalDateTime;
import java.util.List;

public interface daterRepository extends JpaRepository<Cndb, Long> {

    List<Cndb> findByDiaHorarioBetween(LocalDateTime inicio, LocalDateTime fim);

}