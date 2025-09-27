#!/usr/bin/env python3
"""
Linken Sphere API 客户端
用于与 Linken Sphere 指纹浏览器进行集成
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Any
import subprocess
import platform
import os

logger = logging.getLogger(__name__)

class LinkenSphereAPI:
    """Linken Sphere API 客户端类"""

    def __init__(self, api_host: str = "127.0.0.1", api_port: int = 36555, session_port: int = 40080, api_key: str = None):
        """
        初始化 Linken Sphere API 客户端

        Args:
            api_host: API服务器地址
            api_port: API服务器端口（默认36555，基于实际测试结果）
            api_key: API密钥（如果需要）
        """
        self.api_host = api_host
        self.api_port = api_port
        self.api_key = api_key

        # 双端口配置
        self.base_url = f"http://{api_host}:{api_port}"  # 基础API（配置文件等）
        self.session_url = f"http://{api_host}:{session_port}"  # 会话管理

        self.session = requests.Session()

        # 设置请求头
        if api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            })
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None, raw_json: str = None) -> Dict:
        """
        发送API请求

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据（字典格式）
            raw_json: 原始JSON字符串（用于特殊格式要求）

        Returns:
            API响应数据
        """
        # 统一使用36555端口
        url = f"{self.base_url}{endpoint}"

        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            if method.upper() == 'GET':
                response = self.session.get(url, params=data, timeout=30)
            elif method.upper() == 'POST':
                if raw_json:
                    # 发送原始JSON字符串
                    response = self.session.post(url, data=raw_json, headers=headers, timeout=30)
                else:
                    # 发送字典数据
                    response = self.session.post(url, json=data, timeout=30)
            elif method.upper() == 'PUT':
                if raw_json:
                    response = self.session.put(url, data=raw_json, headers=headers, timeout=30)
                else:
                    response = self.session.put(url, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = self.session.delete(url, timeout=30)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()

            # 尝试解析JSON响应
            try:
                return response.json()
            except ValueError:
                # 如果不是JSON，返回文本内容
                return {'text': response.text}

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            raise

    def _make_request_with_timeout(self, method: str, endpoint: str, data: Dict = None, timeout: int = 30) -> Dict:
        """
        发送带自定义超时的API请求

        Args:
            method: HTTP方法
            endpoint: API端点
            data: 请求数据
            timeout: 超时时间（秒）

        Returns:
            API响应数据
        """
        url = f"{self.base_url}{endpoint}"

        try:
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }

            if method.upper() == 'POST':
                response = self.session.post(url, json=data, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            response.raise_for_status()

            # 尝试解析JSON响应
            try:
                return response.json()
            except ValueError:
                # 如果不是JSON，返回文本
                return {'text': response.text, 'success': True}

        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败 (超时={timeout}s): {e}")
            raise

    def check_connection(self) -> bool:
        """
        检查与Linken Sphere的连接状态

        Returns:
            连接是否成功
        """
        try:
            # 基于实际测试，使用可用的端点
            response = self._make_request('GET', '/sessions')

            # 如果能获取到会话列表，说明连接正常
            if isinstance(response, list):
                logger.info(f"✅ Linken Sphere 连接成功，找到 {len(response)} 个配置文件")
                return True
            elif isinstance(response, dict) and response.get('status') == 'ok':
                return True
            else:
                logger.warning("Linken Sphere 响应格式异常")
                return False

        except Exception as e:
            error_msg = str(e)

            # 检查是否是API不可用的错误
            if "API is not available" in error_msg:
                logger.warning("Linken Sphere API 在当前套餐中不可用")
                logger.info("建议升级到支持API的套餐，或使用手动集成模式")
                return False

            # 尝试基础连接测试
            try:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                result = sock.connect_ex((self.api_host, self.api_port))
                sock.close()

                if result == 0:
                    logger.warning("Linken Sphere 服务运行中，但API端点不可用")
                    logger.info("可能的原因：1) API功能未启用 2) 当前套餐不支持API")
                    return False
                else:
                    logger.error("无法连接到Linken Sphere服务")
                    return False

            except Exception:
                logger.error(f"连接检查失败: {e}")
                return False
    
    def get_profiles(self) -> List[Dict]:
        """
        获取所有配置文件

        Returns:
            配置文件列表
        """
        try:
            # 基于实际测试，使用 /sessions 端点获取配置文件
            response = self._make_request('GET', '/sessions')

            if isinstance(response, list):
                # 转换为标准格式，保持uuid字段的一致性
                profiles = []
                for item in response:
                    profile = {
                        'id': item.get('uuid'),
                        'uuid': item.get('uuid'),  # 保持uuid字段
                        'name': item.get('name'),
                        'status': item.get('status', 'unknown')
                    }
                    profiles.append(profile)
                return profiles
            else:
                logger.warning("获取配置文件响应格式异常")
                return []

        except Exception as e:
            logger.error(f"获取配置文件失败: {e}")
            return []
    
    def create_profile(self, profile_config: Dict) -> Dict:
        """
        创建新的配置文件
        
        Args:
            profile_config: 配置文件参数
            
        Returns:
            创建的配置文件信息
        """
        try:
            response = self._make_request('POST', '/api/v1/profiles', profile_config)
            return response
        except Exception as e:
            logger.error(f"创建配置文件失败: {e}")
            raise
    
    def start_session(self, profile_id: str, headless: bool = False, debug_port: int = None) -> Dict:
        """
        启动浏览器会话

        Args:
            profile_id: 配置文件ID（UUID格式）
            headless: 是否无头模式
            debug_port: 调试端口（可选）

        Returns:
            会话信息，包含WebDriver端点
        """
        try:
            # 根据官方实例构建请求数据
            import json

            payload_data = {
                "uuid": profile_id,
                "headless": headless
            }

            # 如果指定了调试端口，添加到请求中
            if debug_port:
                payload_data["debug_port"] = debug_port

            # 转换为JSON字符串（按照官方实例的格式）
            payload_json = json.dumps(payload_data, indent=4)

            logger.info(f"启动浏览器会话，配置文件ID: {profile_id}")
            logger.debug(f"请求数据: {payload_json}")

            # 使用原始JSON字符串发送请求
            response = self._make_request('POST', '/sessions/start', raw_json=payload_json)
            return response
        except Exception as e:
            logger.error(f"启动会话失败: {e}")
            raise
    
    def stop_session(self, profile_uuid: str) -> bool:
        """
        停止浏览器会话

        Args:
            profile_uuid: 配置文件UUID（不是session_id）

        Returns:
            是否成功停止
        """
        try:
            # 根据测试结果，正确的格式是:
            # POST /sessions/stop
            # 数据: {"uuid": "配置文件UUID"}
            # 响应: {"uuid": "配置文件UUID"} (状态码200)

            logger.info(f"停止会话: {profile_uuid}")

            try:
                # 使用正确的格式
                endpoint = '/sessions/stop'
                data = {'uuid': profile_uuid}

                logger.debug(f"停止会话请求: {endpoint}, 数据: {data}")

                # 使用30秒超时，因为停止操作可能需要时间
                response = self._make_request_with_timeout('POST', endpoint, data, timeout=30)

                # 检查响应格式
                if isinstance(response, dict):
                    # 如果响应包含uuid，说明成功
                    if response.get('uuid') == profile_uuid:
                        logger.info(f"成功停止会话 {profile_uuid}")
                        return True
                    # 如果有success字段
                    elif response.get('success', False):
                        logger.info(f"成功停止会话 {profile_uuid}")
                        return True
                    else:
                        logger.warning(f"停止会话响应异常: {response}")
                        return False
                else:
                    logger.warning(f"停止会话响应格式异常: {response}")
                    return False

            except Exception as e:
                logger.error(f"停止会话失败: {e}")

                # 如果是超时错误，可能操作仍在进行
                if "timeout" in str(e).lower():
                    logger.info("停止会话请求超时，但操作可能仍在进行...")
                    # 等待一下再检查状态
                    import time
                    time.sleep(3)

                    # 检查会话状态来确认是否成功
                    try:
                        profiles = self.get_profiles()
                        for profile in profiles:
                            if profile.get('uuid') == profile_uuid:
                                status = profile.get('status', 'unknown')
                                if status == 'stopped':
                                    logger.info("会话已停止，操作成功")
                                    return True
                                else:
                                    logger.warning(f"会话状态: {status}")
                                    return False
                    except:
                        pass

                return False

        except Exception as e:
            logger.error(f"停止会话失败: {e}")
            return False
    
    def get_session_info(self, session_id: str) -> Dict:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话详细信息
        """
        try:
            # 使用统一端口（36555）
            response = self._make_request('GET', f'/info/{session_id}')
            return response
        except Exception as e:
            logger.error(f"获取会话信息失败: {e}")
            return {}

class LinkenSphereProfileManager:
    """Linken Sphere 配置文件管理器"""
    
    def __init__(self, api_client: LinkenSphereAPI):
        self.api = api_client
    
    def create_default_profile(self, name: str = "Apple Browser Profile") -> Dict:
        """
        创建默认的配置文件，适用于Apple网站浏览
        
        Args:
            name: 配置文件名称
            
        Returns:
            创建的配置文件信息
        """
        profile_config = {
            "name": name,
            "browser": "chrome",  # 或 "firefox", "safari"
            "os": self._get_os_config(),
            "screen": {
                "width": 1920,
                "height": 1080
            },
            "timezone": "Asia/Tokyo",  # 适合访问Apple日本网站
            "language": "ja-JP,ja;q=0.9,en;q=0.8",
            "user_agent": self._get_user_agent(),
            "proxy": None,  # 可以后续配置代理
            "webgl": {
                "vendor": "Intel Inc.",
                "renderer": "Intel Iris Pro OpenGL Engine"
            },
            "canvas": {
                "noise": True
            },
            "webrtc": {
                "mode": "altered"
            }
        }
        
        return self.api.create_profile(profile_config)
    
    def _get_os_config(self) -> Dict:
        """获取操作系统配置"""
        system = platform.system()
        if system == "Darwin":  # macOS
            return {
                "name": "macOS",
                "version": "10.15.7"
            }
        elif system == "Windows":
            return {
                "name": "Windows",
                "version": "10"
            }
        else:
            return {
                "name": "Linux",
                "version": "Ubuntu 20.04"
            }
    
    def _get_user_agent(self) -> str:
        """获取适合的User Agent"""
        system = platform.system()
        if system == "Darwin":  # macOS
            return "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        elif system == "Windows":
            return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        else:
            return "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class LinkenSphereManager:
    """Linken Sphere 管理器 - 统一管理API和配置文件"""
    
    def __init__(self, api_host: str = "127.0.0.1", api_port: int = 36555, api_key: str = None):
        self.api = LinkenSphereAPI(api_host, api_port, api_key)
        self.profile_manager = LinkenSphereProfileManager(self.api)
        self.active_sessions = {}
    
    def initialize(self) -> bool:
        """
        初始化Linken Sphere连接
        
        Returns:
            是否初始化成功
        """
        logger.info("正在初始化Linken Sphere连接...")
        
        if not self.api.check_connection():
            logger.error("无法连接到Linken Sphere API")
            return False
        
        logger.info("Linken Sphere连接成功")
        return True
    
    def create_browser_session(self, profile_name: str = "Apple Browser Profile") -> Optional[Dict]:
        """
        创建浏览器会话
        
        Args:
            profile_name: 配置文件名称
            
        Returns:
            会话信息或None
        """
        try:
            # 检查是否已有配置文件
            profiles = self.api.get_profiles()
            profile = None
            
            for p in profiles:
                if p.get('name') == profile_name:
                    profile = p
                    break
            
            # 如果没有配置文件，创建一个
            if not profile:
                logger.info(f"创建新的配置文件: {profile_name}")
                profile = self.profile_manager.create_default_profile(profile_name)
            
            # 启动会话
            profile_id = profile.get('uuid') or profile.get('id')
            logger.info(f"启动浏览器会话，配置文件ID: {profile_id}")
            session = self.api.start_session(profile_id)

            # 保存会话信息（使用UUID作为键）
            session_key = session.get('session_id') or session.get('uuid') or profile_id
            self.active_sessions[session_key] = session

            return session
            
        except Exception as e:
            logger.error(f"创建浏览器会话失败: {e}")
            return None
    
    def close_session(self, session_id: str) -> bool:
        """
        关闭浏览器会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功关闭
        """
        try:
            success = self.api.stop_session(session_id)
            if success and session_id in self.active_sessions:
                del self.active_sessions[session_id]
            return success
        except Exception as e:
            logger.error(f"关闭会话失败: {e}")
            return False
    
    def close_all_sessions(self):
        """关闭所有活动会话"""
        for session_id in list(self.active_sessions.keys()):
            self.close_session(session_id)
