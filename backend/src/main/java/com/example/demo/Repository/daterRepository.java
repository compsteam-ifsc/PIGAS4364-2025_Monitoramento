
package com.example.demo.Repository;

import org.springframework.data.jpa.repository.JpaRepository;

import com.example.demo.ConexaoDb.Cndb;

public interface daterRepository extends JpaRepository<Cndb, Long> {

}