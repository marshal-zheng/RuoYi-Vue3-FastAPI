import os
from datetime import datetime
from fastapi import BackgroundTasks, Request, UploadFile
from typing import List, Dict
from config.env import UploadConfig
from exceptions.exception import ValidationException
from module_admin.entity.vo.common_vo import CrudResponseModel, UploadResponseModel
from utils.upload_util import UploadUtil
from ports import ICommonRepository


class CommonService:
    """
    通用模块服务层
    """

    def __init__(self, common_repo: ICommonRepository):
        self.common_repo = common_repo

    async def upload_service(self, request: Request, file: UploadFile):
        """
        通用上传service

        :param request: Request对象
        :param file: 上传文件对象
        :return: 上传结果
        """
        if not UploadUtil.check_file_extension(file):
            raise ValidationException(
                user_message='文件类型不合法',
                developer_message=f'Invalid file extension: {file.filename}',
                field='file',
            )
        else:
            relative_path = f'upload/{datetime.now().strftime("%Y")}/{datetime.now().strftime("%m")}/{datetime.now().strftime("%d")}'
            dir_path = os.path.join(UploadConfig.UPLOAD_PATH, relative_path)
            try:
                os.makedirs(dir_path)
            except FileExistsError:
                pass
            filename = f'{file.filename.rsplit(".", 1)[0]}_{datetime.now().strftime("%Y%m%d%H%M%S")}{UploadConfig.UPLOAD_MACHINE}{UploadUtil.generate_random_number()}.{file.filename.rsplit(".")[-1]}'
            filepath = os.path.join(dir_path, filename)
            with open(filepath, 'wb') as f:
                # 流式写出大型文件，这里的10代表10MB
                for chunk in iter(lambda: file.file.read(1024 * 1024 * 10), b''):
                    f.write(chunk)

            return CrudResponseModel(
                is_success=True,
                result=UploadResponseModel(
                    fileName=f'{UploadConfig.UPLOAD_PREFIX}/{relative_path}/{filename}',
                    newFileName=filename,
                    originalFilename=file.filename,
                    url=f'{request.base_url}{UploadConfig.UPLOAD_PREFIX[1:]}/{relative_path}/{filename}',
                ),
                message='上传成功',
            )

    async def download_services(self, background_tasks: BackgroundTasks, file_name, delete: bool):
        """
        下载下载目录文件service

        :param background_tasks: 后台任务对象
        :param file_name: 下载的文件名称
        :param delete: 是否在下载完成后删除文件
        :return: 上传结果
        """
        filepath = os.path.join(UploadConfig.DOWNLOAD_PATH, file_name)
        if '..' in file_name:
            raise ValidationException(
                user_message='文件名称不合法',
                developer_message=f'Invalid file name contains ..: {file_name}',
                field='file_name',
            )
        elif not UploadUtil.check_file_exists(filepath):
            raise ValidationException(
                user_message='文件不存在', developer_message=f'File not found: {filepath}', field='file_name'
            )
        else:
            if delete:
                background_tasks.add_task(UploadUtil.delete_file, filepath)
            return CrudResponseModel(is_success=True, result=UploadUtil.generate_file(filepath), message='下载成功')

    async def download_resource_services(self, resource: str):
        """
        下载上传目录文件service

        :param resource: 下载的文件名称
        :return: 上传结果
        """
        filepath = os.path.join(resource.replace(UploadConfig.UPLOAD_PREFIX, UploadConfig.UPLOAD_PATH))
        filename = resource.rsplit('/', 1)[-1]
        if (
            '..' in filename
            or not UploadUtil.check_file_timestamp(filename)
            or not UploadUtil.check_file_machine(filename)
            or not UploadUtil.check_file_random_code(filename)
        ):
            raise ValidationException(
                user_message='文件名称不合法',
                developer_message=f'Invalid file name format: {filename}',
                field='resource',
            )
        elif not UploadUtil.check_file_exists(filepath):
            raise ValidationException(
                user_message='文件不存在', developer_message=f'File not found: {filepath}', field='resource'
            )
        else:
            return CrudResponseModel(is_success=True, result=UploadUtil.generate_file(filepath), message='下载成功')

    async def get_table_names_services(self) -> List[Dict[str, str]]:
        """
        获取数据库中所有表名及其注释

        :return: 表名列表
        """
        return await self.common_repo.list_sys_tables()
