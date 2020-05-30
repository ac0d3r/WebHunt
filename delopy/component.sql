SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `component`;
CREATE TABLE `component` (
  `_id` int(10) unsigned NOT NULL AUTO_INCREMENT COMMENT '_ID，内部自增编号',
  `c_id` varchar(40) NOT NULL COMMENT '组件编号(uuid)',
  `c_name` varchar(64) NOT NULL COMMENT '组件名称',
  `c_first` varchar(10) DEFAULT NULL COMMENT '组件名称首字母',
  `c_type` varchar(32) DEFAULT NULL COMMENT '组件类型',
  `author` varchar(255) DEFAULT NULL COMMENT '组件编写者',
  `version` varchar(10) DEFAULT NULL COMMENT '插件版本',
  `website` varchar(255) DEFAULT NULL COMMENT '组件网站',
  `desc` text COMMENT '组件描述',
  `producer` varchar(100) DEFAULT NULL COMMENT '组件厂商',
  `properties` text COMMENT '组件属性参数(json)',
  `matches` text NOT NULL COMMENT '组件指纹规则(json)',
  `condition` varchar(255) DEFAULT NULL COMMENT '指纹规则组合条件',
  `implies` text COMMENT '依赖的其他组件(string/array)',
  `excludes` text COMMENT '肯定不依赖的其他组件(string/array)',
  
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NULL DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`_id`),
  UNIQUE KEY `c_name` (`c_name`) USING BTREE,
  UNIQUE KEY `c_id` (`c_id`) USING BTREE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


SET FOREIGN_KEY_CHECKS = 1;