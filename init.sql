-- ============================================================
-- 智能任务拆解Agent系统 - 数据库初始化脚本
-- ============================================================
-- 如果使用 docker-compose，MySQL 容器会自动执行此脚本
-- 如果是手动部署，请手动执行此 SQL
-- ============================================================

CREATE DATABASE IF NOT EXISTS task_agent_db
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE task_agent_db;

-- 注意：ORM 会自动建表，此脚本仅用于初始化数据库和字符集设置
-- 表结构由 SQLAlchemy 的 Base.metadata.create_all() 自动创建
