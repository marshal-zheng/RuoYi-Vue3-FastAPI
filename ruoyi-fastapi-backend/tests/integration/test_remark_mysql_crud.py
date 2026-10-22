"""Actual native-JSON CRUD of all seven production ORM mappings in a disposable MySQL database."""

import os
import uuid

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from common.remark_document_v1 import plain_to_remark
from module_admin.entity.do.config_do import ConfigDO
from module_admin.entity.do.dict_do import DictDataDO, DictTypeDO
from module_admin.entity.do.post_do import PostDO
from module_admin.entity.do.role_do import RoleDO
from module_admin.entity.do.user_do import UserDO
from module_generator.entity.do.gen_do import GenTableDO


@pytest.mark.skipif(os.environ.get('RUN_REMARK_MYSQL') != '1', reason='explicit isolated MySQL rehearsal only')
def test_seven_production_mappings_replace_documents_preserve_omission_and_store_sql_null():
    database = f'ruoyi_remark_orm_{uuid.uuid4().hex[:12]}'
    admin = create_engine('mysql+pymysql://root:admin1234@127.0.0.1:3306/mysql')
    with admin.begin() as connection:
        connection.execute(text(f'CREATE DATABASE `{database}` CHARACTER SET utf8mb4'))
    engine = create_engine(f'mysql+pymysql://root:admin1234@127.0.0.1:3306/{database}')
    rows = [
        UserDO(user_id=77, user_name='remark', nick_name='Remark', password='unused'),
        RoleDO(role_id=77, role_name='Remark', role_key='remark', role_sort=1),
        PostDO(post_id=77, post_name='Remark', post_code='remark', post_sort=1),
        DictTypeDO(dict_id=77, dict_name='Remark', dict_type='remark'),
        DictDataDO(dict_code=77, dict_sort=1, dict_label='Label', dict_value='value', dict_type='remark'),
        ConfigDO(config_id=77, config_name='Remark', config_key='remark', config_value='value'),
        GenTableDO(table_id=77, table_name='remark', table_comment='Remark'),
    ]
    try:
        for row in rows:
            row.__table__.create(engine)
        with Session(engine) as session:
            for row in rows:
                row.remark = plain_to_remark('中文😀\n\n <p>=1+1</p> ', identity_key=f'{row.__tablename__}:77:remark')
                session.add(row)
            session.commit()
            for row in rows:
                expected = row.remark
                row.update_by = 'other-fields-only'
                session.commit()
                session.expire_all()
                loaded = session.scalars(select(type(row))).one()
                assert loaded.remark == expected
                assert session.scalar(text(f'SELECT JSON_TYPE(remark) FROM `{row.__tablename__}`')) == 'OBJECT'
                replacement = plain_to_remark('replacement', identity_key=f'{row.__tablename__}:77:remark')
                loaded.remark = replacement
                session.commit()
                session.expire_all()
                assert session.scalars(select(type(row))).one().remark == replacement
                loaded.remark = None
                session.commit()
                assert session.scalar(text(f'SELECT remark IS NULL FROM `{row.__tablename__}`')) == 1
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP DATABASE `{database}`'))
        admin.dispose()
