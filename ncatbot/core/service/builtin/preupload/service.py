"""
预上传服务

提供统一的预上传功能入口，整合消息预上传和文件预上传。
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING
from dataclasses import dataclass

from ncatbot.utils import get_log
from ...base import BaseService
from .client import StreamUploadClient
from .processor import MessagePreUploadProcessor, ProcessResult
from .utils import (
    is_local_file,
    is_base64_data,
    is_remote_url,
    get_local_path,
    extract_base64_data,
    generate_filename_from_type,
)
from .constants import DEFAULT_CHUNK_SIZE, DEFAULT_FILE_RETENTION

if TYPE_CHECKING:
    from ..websocket import WebSocketService

LOG = get_log("PreUploadService")


@dataclass
class PreUploadResult:
    """预上传结果"""
    success: bool
    file_path: Optional[str] = None
    original_path: Optional[str] = None
    error: Optional[str] = None
    
    @property
    def uploaded(self) -> bool:
        """是否执行了上传"""
        return self.success and self.file_path != self.original_path


class PreUploadService(BaseService):
    """
    预上传服务
    
    提供统一的预上传功能：
    - 消息预上传：处理消息结构中的所有可上传资源
    - 文件预上传：单独上传文件并返回服务器路径
    
    内部使用 StreamUploadClient 进行实际的文件传输。
    """
    
    name = "preupload"
    description = "消息和文件预上传服务"
    
    def __init__(
        self,
        ws_service: Optional["WebSocketService"] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        file_retention: int = DEFAULT_FILE_RETENTION,
        **config
    ):
        """
        Args:
            ws_service: WebSocket 服务实例
            chunk_size: 分片大小（字节）
            file_retention: 文件保留时间（毫秒）
        """
        super().__init__(**config)
        self._ws_service = ws_service
        self._chunk_size = chunk_size
        self._file_retention = file_retention
        self._client: Optional[StreamUploadClient] = None
        self._message_processor: Optional[MessagePreUploadProcessor] = None
    
    def set_websocket_service(self, ws_service: "WebSocketService") -> None:
        """设置 WebSocket 服务"""
        self._ws_service = ws_service
        if self._loaded:
            self._init_components()
    
    async def on_load(self) -> None:
        """服务加载"""
        if not self._ws_service:
            LOG.warning("WebSocket 服务未设置，预上传功能不可用")
            return
        
        self._init_components()
        LOG.info("预上传服务已加载")
    
    async def on_close(self) -> None:
        """服务关闭"""
        self._message_processor = None
        self._client = None
        LOG.info("预上传服务已关闭")
    
    def _init_components(self) -> None:
        """初始化内部组件"""
        if not self._ws_service:
            return
        
        self._client = StreamUploadClient(
            self._ws_service,
            self._chunk_size,
            self._file_retention
        )
        self._message_processor = MessagePreUploadProcessor(self._client)
    
    # -------------------------------------------------------------------------
    # 底层上传接口
    # -------------------------------------------------------------------------
    
    async def upload_file(self, file_path: str):
        """
        上传本地文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            UploadResult: 上传结果
        """
        from .client import UploadResult
        if not self._client:
            return UploadResult(success=False, error="预上传服务未初始化")
        return await self._client.upload_file(file_path)
    
    async def upload_bytes(self, data: bytes, filename: str):
        """
        上传字节数据
        
        Args:
            data: 字节数据
            filename: 文件名
            
        Returns:
            UploadResult: 上传结果
        """
        from .client import UploadResult
        if not self._client:
            return UploadResult(success=False, error="预上传服务未初始化")
        return await self._client.upload_bytes(data, filename)
    
    # -------------------------------------------------------------------------
    # 消息预上传接口
    # -------------------------------------------------------------------------
    
    async def process_message(
        self, 
        data: Dict[str, Any]
    ) -> ProcessResult:
        """
        处理消息数据，上传所有需要预上传的文件
        
        Args:
            data: 序列化后的消息字典
            
        Returns:
            ProcessResult: 处理结果
        """
        if not self._message_processor:
            return ProcessResult(
                success=False,
                errors=["预上传服务未初始化"]
            )
        return await self._message_processor.process(data)
    
    async def process_message_array(
        self, 
        messages: List[Dict[str, Any]]
    ) -> ProcessResult:
        """
        处理消息数组
        
        Args:
            messages: 消息段列表
            
        Returns:
            ProcessResult: 处理结果
        """
        if not self._message_processor:
            return ProcessResult(
                success=False,
                errors=["预上传服务未初始化"]
            )
        return await self._message_processor.process_message_array(messages)
    
    # -------------------------------------------------------------------------
    # 文件预上传接口
    # -------------------------------------------------------------------------
    
    async def preupload_file(
        self, 
        file_value: str, 
        file_type: str = "file"
    ) -> PreUploadResult:
        """
        预上传单个文件
        
        Args:
            file_value: 文件路径、Base64 数据或 URL
            file_type: 文件类型（image/video/record/file）
            
        Returns:
            PreUploadResult: 预上传结果
        """
        if not self._client:
            return PreUploadResult(
                success=False,
                error="预上传服务未初始化"
            )
        
        if not file_value:
            return PreUploadResult(
                success=False,
                error="文件路径为空"
            )
        
        # 远程 URL 不需要上传
        if is_remote_url(file_value):
            return PreUploadResult(
                success=True,
                file_path=file_value,
                original_path=file_value
            )
        
        # 本地文件上传
        if is_local_file(file_value):
            return await self._upload_local(file_value)
        
        # Base64 数据上传
        if is_base64_data(file_value):
            return await self._upload_base64(file_value, file_type)
        
        # 未知格式，直接返回
        return PreUploadResult(
            success=True,
            file_path=file_value,
            original_path=file_value
        )
    
    async def preupload_file_if_needed(
        self, 
        file_value: str, 
        file_type: str = "file"
    ) -> str:
        """
        如果需要则预上传文件，返回最终路径
        
        Args:
            file_value: 文件路径、Base64 数据或 URL
            file_type: 文件类型
            
        Returns:
            str: 最终的文件路径
            
        Raises:
            RuntimeError: 预上传失败时抛出
        """
        result = await self.preupload_file(file_value, file_type)
        
        if not result.success:
            raise RuntimeError(f"文件预上传失败: {result.error}")
        
        return result.file_path
    
    async def _upload_local(self, file_value: str) -> PreUploadResult:
        """上传本地文件"""
        local_path = get_local_path(file_value)
        if not local_path:
            return PreUploadResult(
                success=False,
                original_path=file_value,
                error="无法解析本地文件路径"
            )
        
        result = await self._client.upload_file(local_path)
        
        if result.success:
            LOG.debug(f"文件预上传成功: {local_path} -> {result.file_path}")
            return PreUploadResult(
                success=True,
                file_path=result.file_path,
                original_path=file_value
            )
        
        return PreUploadResult(
            success=False,
            original_path=file_value,
            error=result.error
        )
    
    async def _upload_base64(
        self, 
        file_value: str, 
        file_type: str
    ) -> PreUploadResult:
        """上传 Base64 数据"""
        data = extract_base64_data(file_value)
        if not data:
            return PreUploadResult(
                success=False,
                original_path=file_value,
                error="Base64 解码失败"
            )
        
        filename = generate_filename_from_type(file_type)
        result = await self._client.upload_bytes(data, filename)
        
        if result.success:
            LOG.debug(f"Base64 预上传成功: {file_value[:30]}... -> {result.file_path}")
            return PreUploadResult(
                success=True,
                file_path=result.file_path,
                original_path=file_value
            )
        
        return PreUploadResult(
            success=False,
            original_path=file_value,
            error=result.error
        )
    
    # -------------------------------------------------------------------------
    # 属性访问
    # -------------------------------------------------------------------------
    
    @property
    def client(self) -> Optional[StreamUploadClient]:
        """获取上传客户端"""
        return self._client
    
    @property
    def message_processor(self) -> Optional[MessagePreUploadProcessor]:
        """获取消息处理器"""
        return self._message_processor
    
    @property
    def available(self) -> bool:
        """服务是否可用"""
        return self._loaded and self._client is not None
