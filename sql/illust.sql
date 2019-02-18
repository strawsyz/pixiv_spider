/*
Navicat MySQL Data Transfer

Source Server         : my
Source Server Version : 50722
Source Host           : localhost:3306
Source Database       : test

Target Server Type    : MYSQL
Target Server Version : 50722
File Encoding         : 65001

Date: 2019-02-18 13:02:49
*/

SET FOREIGN_KEY_CHECKS=0;

-- ----------------------------
-- Table structure for illust
-- ----------------------------
DROP TABLE IF EXISTS `illust`;
CREATE TABLE `illust` (
  `id` bigint(20) NOT NULL AUTO_INCREMENT,
  `title` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `url` varchar(255) COLLATE utf8_bin DEFAULT NULL,
  `illust_id` bigint(20) DEFAULT NULL,
  `illuster_id` bigint(20) DEFAULT NULL,
  `page_no` int(11) DEFAULT NULL,
  `status` int(11) DEFAULT '0',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=12695 DEFAULT CHARSET=utf8 COLLATE=utf8_bin;
