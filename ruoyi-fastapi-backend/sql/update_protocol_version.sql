-- 协议表版本字段升级脚本（向下兼容版）
-- 目标：在不影响现有业务读取 `version` 字段的前提下，引入 `version_number` 与 `remark`

START TRANSACTION;

SET @need_add_version := (
    SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'sys_protocol'
      AND COLUMN_NAME = 'version'
);

SET @ddl_version = IF(
    @need_add_version = 1,
    'ALTER TABLE `sys_protocol` ADD COLUMN `version` varchar(50) NOT NULL DEFAULT ''1.0'' COMMENT ''版本号'' AFTER `protocol_type`;',
    'DO 0;'
);
PREPARE stmt FROM @ddl_version;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @need_add_version_number := (
    SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'sys_protocol'
      AND COLUMN_NAME = 'version_number'
);

SET @ddl_version_number = IF(
    @need_add_version_number = 1,
    'ALTER TABLE `sys_protocol` ADD COLUMN `version_number` int(11) NOT NULL DEFAULT 1 COMMENT ''版本号（系统自动管理，从1开始递增）'' AFTER `version`;',
    'DO 0;'
);
PREPARE stmt FROM @ddl_version_number;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @need_add_remark := (
    SELECT CASE WHEN COUNT(*) = 0 THEN 1 ELSE 0 END
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'sys_protocol'
      AND COLUMN_NAME = 'remark'
);

SET @ddl_remark = IF(
    @need_add_remark = 1,
    'ALTER TABLE `sys_protocol` ADD COLUMN `remark` varchar(500) DEFAULT NULL COMMENT ''版本备注'' AFTER `protocol_config`;',
    'DO 0;'
);
PREPARE stmt FROM @ddl_remark;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 迁移旧数据（仅在 version 存在有效值时同步）
UPDATE `sys_protocol`
SET `version_number` = CAST(SUBSTRING_INDEX(REPLACE(`version`, 'v', ''), '.', 1) AS UNSIGNED)
WHERE (`version` REGEXP '^[vV]?[0-9]+(\\.[0-9]+)*$')
  AND (`version_number` IS NULL OR `version_number` = 1);

UPDATE `sys_protocol`
SET `version_number` = 1
WHERE `version_number` IS NULL OR `version_number` <= 0;

-- 复合索引处理
SET @has_old_index := (
    SELECT CASE WHEN COUNT(*) > 0 THEN 1 ELSE 0 END
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = 'sys_protocol'
      AND INDEX_NAME = 'idx_protocol_name_version'
);

SET @ddl_drop_index = IF(
    @has_old_index = 1,
    'ALTER TABLE `sys_protocol` DROP INDEX `idx_protocol_name_version`;',
    'DO 0;'
);
PREPARE stmt FROM @ddl_drop_index;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

ALTER TABLE `sys_protocol`
ADD KEY `idx_protocol_name_version` (`protocol_name`, `version_number`);

-- 默认备注
UPDATE `sys_protocol`
SET `remark` = '初始版本'
WHERE `remark` IS NULL OR `remark` = '';

COMMIT;
