from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
from typing import Dict, Optional
import time
import asyncio
import logging

from src.core.database import db_manager

logger = logging.getLogger(__name__)

try:
    from src.api.auth.jwt_handler import JWTHandler
except ImportError:
    JWTHandler = None
    logger.warning("JWTHandler not found, JWT token extraction will be skipped")


class LoggingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        try:
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            asyncio.create_task(self._log_in_background(request, response, process_time))

            return response
        except Exception as e:
            logger.error(f"LoggingMiddleware error: {e}")
            return await call_next(request)

    async def _log_in_background(self, request: Request, response: Response, process_time: float):
        try:
            if not await db_manager.is_mongo_healthy():
                logger.warning("MongoDB not connected, skipping API log")
                return

            method = request.method
            url = str(request.url)
            ip_address = getattr(request.client, 'host', None) if request.client else None
            user_agent = request.headers.get("user-agent")

            log_entry = {
                "timestamp": datetime.utcnow(),
                "type": "api_request",
                "method": method,
                "url": url,
                "status_code": response.status_code,
                "process_time": round(process_time, 3),
                "ip_address": ip_address,
                "user_agent": user_agent
            }

            await db_manager.log_to_mongo("app_logs", log_entry)
            logger.debug(f"Logged API request to MongoDB: {log_entry}")

        except Exception as e:
            logger.error(f"Background logging failed: {e}")


class RequestActionMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        try:
            if not self._is_request_action(request):
                return await call_next(request)

            response = await call_next(request)

            if 200 <= response.status_code < 300:
                asyncio.create_task(self._log_action_background(request, response))

            return response
        except Exception as e:
            logger.error(f"RequestActionMiddleware error: {e}")
            return await call_next(request)

    def _is_request_action(self, request: Request) -> bool:
        try:
            url_path = request.url.path
            return (
                    ("/user_request/" in url_path or "/staff/requests" in url_path)
                    and request.method in ["GET", "POST", "PUT", "PATCH", "DELETE"]
            )
        except:
            return False

    async def _log_action_background(self, request: Request, response: Response):
        try:
            if not await db_manager.is_mongo_healthy():
                logger.error("MongoDB not connected, skipping request_action log")
                return

            user_info = await self._extract_user_info(request)
            if not user_info:
                return

            request_id = self._extract_request_id(request)
            action = self._determine_action(request)

            log_entry = {
                "timestamp": datetime.utcnow(),
                "type": "request_action",
                "request_id": request_id,
                "user_id": user_info.get("user_id"),
                "user_email": user_info.get("email"),
                "user_role": user_info.get("role"),
                "action": action,
                "method": request.method,
                "url": str(request.url)
            }

            await db_manager.log_to_mongo("request_actions", log_entry)
        except Exception as e:
            logger.error(f"Action logging failed: {e}")

    def _extract_request_id(self, request: Request) -> Optional[int]:
        try:
            path_parts = request.url.path.split("/")

            if "user_request" in path_parts:
                index = path_parts.index("user_request")
                if index + 1 < len(path_parts) and path_parts[index + 1].isdigit():
                    return int(path_parts[index + 1])

            if "requests" in path_parts:
                index = path_parts.index("requests")
                if index + 1 < len(path_parts) and path_parts[index + 1].isdigit():
                    return int(path_parts[index + 1])

        except:
            pass
        return None

    def _determine_action(self, request: Request) -> str:
        try:
            method = request.method
            url_path = request.url.path

            if "/user_request/" in url_path:
                if method == "POST" and url_path.endswith("/user_request/"):
                    return "create_request"
                elif method == "GET":
                    if url_path.endswith("/my"):
                        return "view_my_requests"
                    elif url_path.count("/") > 2:
                        return "view_request"
                    else:
                        return "list_requests"
                elif method in ["PUT", "PATCH"]:
                    return "update_request"
                elif method == "DELETE":
                    return "delete_request"

            elif "/staff/requests" in url_path or "/admin/requests" in url_path:
                if method == "GET":
                    return "view_request" if url_path.count("/") > 3 else "list_assigned_requests"
                elif method in ["PUT", "PATCH"]:
                    if "assign" in url_path:
                        return "assign_request"
                    elif "status" in url_path:
                        return "change_status"
                    else:
                        return "manage_request"
                elif method == "DELETE":
                    return "admin_delete_request"

            return "unknown_action"
        except:
            return "unknown_action"

    async def _extract_user_info(self, request: Request) -> Optional[Dict]:
        try:
            if JWTHandler is None:
                return None

            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.split(" ")[1]
            payload = JWTHandler.decode_token(token)

            if payload and "role" in payload:
                payload["role"] = payload["role"].upper()

            return payload
        except:
            return None