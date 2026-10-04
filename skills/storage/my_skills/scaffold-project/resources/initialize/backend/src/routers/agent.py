from __future__ import annotations

from fastapi import APIRouter, Depends
from src.config import Settings, setup_logger
from src.schema import AgentRequest, AgentResponse, AgentProfile
from src.services import AgentService
from src.routers.dependencies import get_current_user
from src.db import User

logger = setup_logger(boss_name="routers.main.txt", his_name="routers.agent.txt")
router = APIRouter(prefix="/api/agent", tags=["agent"])


def get_agent_service() -> AgentService:
    return AgentService()


@router.post("/run", response_model=AgentResponse)
async def run_agent(
    body: AgentRequest,
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> AgentResponse:
    logger.info(f"User {current_user.id} requested agent execution")
    return await service.execute(body)


@router.get("/list", response_model=list[AgentProfile])
async def list_agents(
    current_user: User = Depends(get_current_user),
    service: AgentService = Depends(get_agent_service),
) -> list[AgentProfile]:
    return service.list_agents()
