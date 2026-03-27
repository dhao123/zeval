"""
Aliyun OSS Service for file upload and download.
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional

import oss2
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class OSSService:
    """阿里云OSS服务"""
    
    def __init__(self):
        self.access_key_id = settings.oss_access_key_id
        self.access_key_secret = settings.oss_access_key_secret
        self.endpoint = settings.oss_endpoint
        self.bucket_name = settings.oss_bucket_name
        
        # 初始化OSS客户端
        if self.access_key_id and self.access_key_secret:
            self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)
            self.bucket = oss2.Bucket(self.auth, self.endpoint, self.bucket_name)
        else:
            self.auth = None
            self.bucket = None
            logger.warning("OSS credentials not configured")
    
    def is_configured(self) -> bool:
        """检查OSS是否已配置"""
        return self.bucket is not None
    
    def generate_object_key(self, filename: str, folder: str = "uploads") -> str:
        """
        生成OSS对象存储路径
        
        格式: {folder}/YYYY/MM/DD/{uuid}_{filename}
        """
        now = datetime.now()
        date_path = now.strftime("%Y/%m/%d")
        unique_id = uuid.uuid4().hex[:12]
        
        # 清理文件名，只保留安全字符
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._-")
        
        return f"{folder}/{date_path}/{unique_id}_{safe_filename}"
    
    async def upload_file(
        self,
        file_content: bytes,
        filename: str,
        folder: str = "uploads"
    ) -> tuple[str, str]:
        """
        上传文件到OSS
        
        Args:
            file_content: 文件内容(bytes)
            filename: 原始文件名
            folder: 存储文件夹
            
        Returns:
            (object_key, file_url): OSS对象键和访问URL
        """
        if not self.is_configured():
            raise RuntimeError("OSS not configured")
        
        object_key = self.generate_object_key(filename, folder)
        
        try:
            # 上传文件
            result = self.bucket.put_object(object_key, file_content)
            
            if result.status == 200:
                # 生成访问URL
                file_url = self.bucket.sign_url('GET', object_key, 3600 * 24 * 7)  # 7天有效期
                logger.info(f"File uploaded to OSS: {object_key}")
                return object_key, file_url
            else:
                raise RuntimeError(f"Upload failed with status: {result.status}")
                
        except Exception as e:
            logger.error(f"OSS upload failed: {e}")
            raise
    
    async def upload_file_object(self, file_obj, object_key: str) -> str:
        """
        上传文件对象到OSS指定路径
        
        Args:
            file_obj: 文件对象(支持BytesIO或file-like对象)
            object_key: OSS对象键(完整路径)
            
        Returns:
            file_url: 访问URL
        """
        if not self.is_configured():
            raise RuntimeError("OSS not configured")
        
        try:
            # 读取文件内容
            if hasattr(file_obj, 'read'):
                content = file_obj.read()
            else:
                content = file_obj
            
            # 上传文件
            result = self.bucket.put_object(object_key, content)
            
            if result.status == 200:
                # 生成访问URL (7天有效期)
                file_url = self.bucket.sign_url('GET', object_key, 3600 * 24 * 7)
                logger.info(f"File uploaded to OSS: {object_key}")
                return file_url
            else:
                raise RuntimeError(f"Upload failed with status: {result.status}")
                
        except Exception as e:
            logger.error(f"OSS upload failed: {e}")
            raise
    
    def get_signed_url(self, object_key: str, expire_seconds: int = 3600) -> str:
        """
        获取带签名的临时访问URL
        
        Args:
            object_key: OSS对象键
            expire_seconds: 过期时间（秒）
            
        Returns:
            签名URL
        """
        if not self.is_configured():
            raise RuntimeError("OSS not configured")
        
        return self.bucket.sign_url('GET', object_key, expire_seconds)
    
    def delete_file(self, object_key: str) -> bool:
        """
        删除OSS文件
        
        Args:
            object_key: OSS对象键
            
        Returns:
            是否删除成功
        """
        if not self.is_configured():
            return False
        
        try:
            self.bucket.delete_object(object_key)
            logger.info(f"File deleted from OSS: {object_key}")
            return True
        except Exception as e:
            logger.error(f"OSS delete failed: {e}")
            return False
    
    def get_object_content(self, object_key: str) -> bytes:
        """
        获取OSS文件内容
        
        Args:
            object_key: OSS对象键
            
        Returns:
            文件内容(bytes)
        """
        if not self.is_configured():
            raise RuntimeError("OSS not configured")
        
        result = self.bucket.get_object(object_key)
        return result.read()


# 全局OSS服务实例
oss_service = OSSService()


def get_oss_service() -> OSSService:
    """获取OSS服务实例"""
    return oss_service
