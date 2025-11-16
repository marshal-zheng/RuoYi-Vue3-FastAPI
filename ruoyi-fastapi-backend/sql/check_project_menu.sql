-- 查询工程管理相关的菜单数据
SELECT 
    menu_id,
    menu_name,
    parent_id,
    order_num,
    path,
    component,
    menu_type,
    perms,
    icon,
    remark
FROM sys_menu 
WHERE menu_name LIKE '%工程%' OR menu_name LIKE '%操作日志%'
ORDER BY parent_id, order_num;
