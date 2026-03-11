DROP TABLE IF EXISTS `horario`;

CREATE TABLE `horario` (
  `id` int NOT NULL AUTO_INCREMENT,
  `dia_horario` datetime NOT NULL,
  `Saida_chegada` varchar(1) NOT NULL,
  PRIMARY KEY (`id`)
);



