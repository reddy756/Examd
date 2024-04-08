-- MySQL dump 10.13  Distrib 8.0.33, for Win64 (x86_64)
--
-- Host: localhost    Database: invigila
-- ------------------------------------------------------
-- Server version	8.0.33

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `courses`
--

DROP TABLE IF EXISTS `courses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `courses` (
  `course_id` int NOT NULL AUTO_INCREMENT,
  `course_name` varchar(255) NOT NULL,
  `department_id` int DEFAULT NULL,
  PRIMARY KEY (`course_id`),
  KEY `department_id` (`department_id`),
  CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`department_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `courses`
--

LOCK TABLES `courses` WRITE;
/*!40000 ALTER TABLE `courses` DISABLE KEYS */;
INSERT INTO `courses` VALUES (1,'Technology',1),(2,'Calculus I',2),(3,'Mechanics',3),(4,'Organic Chemistry',4),(5,'Cell Biology',5),(6,'English Literature',6),(7,'World History',7),(8,'Physical Geography',8),(9,'Political Theory',9),(12,'Database',1),(13,'DLD',1);
/*!40000 ALTER TABLE `courses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `departments`
--

DROP TABLE IF EXISTS `departments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `departments` (
  `department_id` int NOT NULL AUTO_INCREMENT,
  `department_name` varchar(60) NOT NULL,
  `incharge_user_id` int DEFAULT NULL,
  PRIMARY KEY (`department_id`),
  KEY `incharge_user_id` (`incharge_user_id`),
  CONSTRAINT `departments_ibfk_1` FOREIGN KEY (`incharge_user_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `departments`
--

LOCK TABLES `departments` WRITE;
/*!40000 ALTER TABLE `departments` DISABLE KEYS */;
INSERT INTO `departments` VALUES (1,'Computer Science',5),(2,'Mathematics',3),(3,'Physics',2),(4,'Chemistry',NULL),(5,'Biology',NULL),(6,'English',NULL),(7,'History',21),(8,'Geography',NULL),(9,'Political Science',10),(11,'Economics',4);
/*!40000 ALTER TABLE `departments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `faculty`
--

DROP TABLE IF EXISTS `faculty`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `faculty` (
  `faculty_id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `department_id` int DEFAULT NULL,
  `course_id` int DEFAULT NULL,
  PRIMARY KEY (`faculty_id`),
  KEY `user_id` (`user_id`),
  KEY `department_id` (`department_id`),
  KEY `course_id` (`course_id`),
  CONSTRAINT `faculty_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `faculty_ibfk_2` FOREIGN KEY (`department_id`) REFERENCES `departments` (`department_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `faculty_ibfk_3` FOREIGN KEY (`course_id`) REFERENCES `courses` (`course_id`) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `faculty`
--

LOCK TABLES `faculty` WRITE;
/*!40000 ALTER TABLE `faculty` DISABLE KEYS */;
INSERT INTO `faculty` VALUES (11,2,9,9),(12,3,2,2),(13,4,3,3),(14,5,4,4),(15,6,5,5),(16,7,6,6),(17,8,7,7),(18,9,8,8),(19,10,9,9),(20,13,2,2),(25,18,9,9),(26,20,6,6),(27,21,7,7);
/*!40000 ALTER TABLE `faculty` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('Admin','Department Incharge','Faculty') NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (2,'John Deo','john.doe@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Faculty'),(3,'Jane Doe','jane.doe@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Department Incharge'),(4,'Mike Smith','mike.smith@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Department Incharge'),(5,'Emily Jones','emily.jones@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Department Incharge'),(6,'David Brown','david.brown@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Faculty'),(7,'Lisa Taylor','lisa.taylor@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Faculty'),(8,'James Wilson','james.wilson@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Faculty'),(9,'Laura Moore','laura.moore@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Department Incharge'),(10,'Robert Miller','robert.miller@example.com','pbkdf2:sha256:600000$llhFUduNn20pljeA$751816b7965a45db4e59e53e8a035eacaf24c43d7e2724075e86eade055c7fd7','Department Incharge'),(13,'Bharath','bhaskerdareddy75@gmail.com','pbkdf2:sha256:600000$WgFbsSM6toB7BiB2$bd79715f0e263905cc68a8a591c33c0d0504f0ba3b9084be7f3d0eb7c02ae3ce','Faculty'),(18,'Dareddy Bhaskar reddy121','velab39759@evimzo.com','pbkdf2:sha256:600000$5rwXAJ98j3Cz8BL0$4313474c8f4df18e790105ad523634ca7df6dab73e65e94960f6db25cb8fb47e','Faculty'),(19,'Bhaskar','dbsreddy3@gmail.com','pbkdf2:sha256:600000$pbmZkEWlRjdccbGp$f932f1991edb3fb6452e5921c0c567f9ce6b79c6f02e1d9438436dc79b658bd6','Admin'),(20,'Bhaskar123','20jk1a0508@gmail.com','pbkdf2:sha256:600000$IhhwOy0eokmIlxnr$7603f068bb69be09927fc50b49e65168f37beca71903ed38f3517fc5ec80b19c','Faculty'),(21,'Rajini','gollapudirajini514@gmail.com','pbkdf2:sha256:600000$0j3ATaebv6YEYznx$00b62808b7d9430c0fb6a0414554a707fd58d8a6cb25a863b3ae71870e73f404','Department Incharge');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2024-04-04 15:09:15
