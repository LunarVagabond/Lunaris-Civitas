"""Human-related systems for Phase 2 (Base Human - Minimal Survival)."""

from src.systems.human.requirement_resolver import RequirementResolverSystem
from src.systems.human.spawn import HumanSpawnSystem
from src.systems.human.needs import NeedsSystem
from src.systems.human.needs_fulfillment import HumanNeedsFulfillmentSystem
from src.systems.human.health import HealthSystem
from src.systems.human.death import DeathSystem

__all__ = [
    'RequirementResolverSystem',
    'HumanSpawnSystem',
    'NeedsSystem',
    'HumanNeedsFulfillmentSystem',
    'HealthSystem',
    'DeathSystem'
]
