"""Requirement resolver system for resolving resource requirements.

Resolves resource requirements by trying multiple sources in priority order.
Handles contextual requirements where the same need can be met through
different paths (inventory, household, market, production).
"""

from datetime import datetime
from typing import Dict, List, Any, Optional

from src.core.system import System
from src.models.entity import Entity
from src.models.requirement_source import RequirementSource
from src.models.requirement_resolution import RequirementResolution
from src.core.world_state import WorldState


class RequirementResolverSystem(System):
    """Resolves resource requirements by trying multiple sources in priority order.
    
    This system handles the complexity of contextual requirements:
    - Food might come from inventory (no requirement)
    - Or from market (requires money)
    - Or from production (requires seeds, if farmer)
    - Or from household (no requirement, shared stock)
    """
    
    @property
    def system_id(self) -> str:
        return "RequirementResolver"
    
    def __init__(self):
        """Initialize requirement resolver system."""
        # Source definitions loaded from config
        # Maps resource_id -> list of sources (sorted by priority)
        self.source_definitions: Dict[str, List[RequirementSource]] = {}
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Load requirement source definitions from config.
        
        Args:
            world_state: World state instance
            config: System configuration dictionary
            
        Example config structure:
            requirement_sources:
              food:
                - source_id: inventory
                  source_type: inventory
                  priority: 1
                  conditions: {has_component: "Inventory"}
                  requirements: {}
                  fulfillment_method: "consume_from_inventory"
                - source_id: market
                  source_type: market
                  priority: 3
                  conditions: {has_component: "Wealth"}
                  requirements: {money: 5.0}
                  fulfillment_method: "purchase_from_market"
        """
        requirement_sources = config.get('requirement_sources', {})
        
        for resource_id, sources_list in requirement_sources.items():
            sources = []
            for source_config in sources_list:
                source = RequirementSource(
                    source_id=source_config['source_id'],
                    source_type=source_config['source_type'],
                    priority=source_config['priority'],
                    conditions=source_config.get('conditions', {}),
                    requirements=source_config.get('requirements', {}),
                    fulfillment_method=source_config.get('fulfillment_method', 'consume')
                )
                sources.append(source)
            
            # Sort by priority (lower priority = tried first)
            sources.sort(key=lambda s: s.priority)
            self.source_definitions[resource_id] = sources
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        This system doesn't process automatically - it's called by other systems
        when they need to resolve requirements.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        # This system is passive - it's called by other systems
        pass
    
    def resolve_requirement(
        self,
        entity: Entity,
        resource_id: str,
        amount: float,
        world_state: WorldState
    ) -> RequirementResolution:
        """Resolve a resource requirement by trying sources in order.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            world_state: World state for context
            
        Returns:
            RequirementResolution with success status, source used, amount fulfilled
        """
        sources = self.source_definitions.get(resource_id, [])
        
        # Fallback: If no sources configured, try direct world resource consumption
        # This is a Phase 2 fallback - in later phases, sources should be configured
        if not sources:
            return self._fulfill_from_world_fallback(entity, resource_id, amount, world_state)
        
        for source in sources:
            # Check if source is available
            if not source.is_available(entity, world_state):
                continue
            
            # Check if source can fulfill
            can_fulfill, reason = source.can_fulfill(entity, resource_id, amount, world_state)
            if not can_fulfill:
                continue
            
            # Attempt fulfillment
            fulfilled = self._fulfill_through_source(
                entity, resource_id, amount, source, world_state
            )
            
            if fulfilled > 0:
                return RequirementResolution(
                    success=True,
                    source_id=source.source_id,
                    amount_fulfilled=fulfilled,
                    amount_requested=amount
                )
        
        # All sources failed
        return RequirementResolution(
            success=False,
            source_id=None,
            amount_fulfilled=0.0,
            amount_requested=amount,
            reason="All sources failed"
        )
    
    def _fulfill_through_source(
        self,
        entity: Entity,
        resource_id: str,
        amount: float,
        source: RequirementSource,
        world_state: WorldState
    ) -> float:
        """Fulfill requirement through a specific source.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            source: Source to use for fulfillment
            world_state: World state for context
            
        Returns:
            Amount actually fulfilled (may be less than requested)
        """
        if source.source_type == 'inventory':
            return self._fulfill_from_inventory(entity, resource_id, amount)
        
        elif source.source_type == 'household':
            return self._fulfill_from_household(entity, resource_id, amount, world_state)
        
        elif source.source_type == 'market':
            return self._fulfill_from_market(entity, resource_id, amount, source, world_state)
        
        elif source.source_type == 'production':
            return self._fulfill_from_production(entity, resource_id, amount, source, world_state)
        
        else:
            return 0.0
    
    def _fulfill_from_inventory(
        self,
        entity: Entity,
        resource_id: str,
        amount: float
    ) -> float:
        """Fulfill requirement from entity's inventory.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            
        Returns:
            Amount actually fulfilled
        """
        inventory = entity.get_component('Inventory')
        if inventory is None:
            return 0.0
        
        if inventory.remove_resource(resource_id, amount):
            return amount
        
        # Try to fulfill as much as possible
        available = inventory.get_amount(resource_id)
        if available > 0:
            inventory.remove_resource(resource_id, available)
            return available
        
        return 0.0
    
    def _fulfill_from_household(
        self,
        entity: Entity,
        resource_id: str,
        amount: float,
        world_state: WorldState
    ) -> float:
        """Fulfill requirement from household inventory.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            world_state: World state for context
            
        Returns:
            Amount actually fulfilled
        """
        household = entity.get_component('Household')
        if household is None:
            return 0.0
        
        household_id = getattr(household, 'household_id', None)
        if household_id is None:
            return 0.0
        
        household_entity = world_state.get_entity(household_id)
        if household_entity is None:
            return 0.0
        
        household_inventory = household_entity.get_component('Inventory')
        if household_inventory is None:
            return 0.0
        
        if household_inventory.remove_resource(resource_id, amount):
            return amount
        
        # Try to fulfill as much as possible
        available = household_inventory.get_amount(resource_id)
        if available > 0:
            household_inventory.remove_resource(resource_id, available)
            return available
        
        return 0.0
    
    def _fulfill_from_market(
        self,
        entity: Entity,
        resource_id: str,
        amount: float,
        source: RequirementSource,
        world_state: WorldState
    ) -> float:
        """Fulfill requirement by purchasing from market.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            source: Market source definition
            world_state: World state for context
            
        Returns:
            Amount actually fulfilled
        """
        wealth = entity.get_component('Wealth')
        if wealth is None:
            return 0.0
        
        # Calculate cost
        cost_per_unit = source.requirements.get('money', 0.0)
        total_cost = cost_per_unit * amount
        
        # Check if entity has enough money
        if not hasattr(wealth, 'money') or wealth.money < total_cost:
            return 0.0
        
        # Check if global resource exists and has enough
        global_resource = world_state.get_resource(resource_id)
        if global_resource is None:
            return 0.0
        
        if global_resource.current_amount < amount:
            # Try to fulfill as much as possible
            available = global_resource.current_amount
            if available > 0:
                actual_cost = cost_per_unit * available
                if wealth.money >= actual_cost:
                    global_resource.consume(available)
                    wealth.money -= actual_cost
                    return available
            return 0.0
        
        # Fulfill full amount
        global_resource.consume(amount)
        wealth.money -= total_cost
        
        return amount
    
    def _fulfill_from_production(
        self,
        entity: Entity,
        resource_id: str,
        amount: float,
        source: RequirementSource,
        world_state: WorldState
    ) -> float:
        """Fulfill requirement by producing through job.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            source: Production source definition
            world_state: World state for context
            
        Returns:
            Amount actually fulfilled
        """
        inventory = entity.get_component('Inventory')
        if inventory is None:
            return 0.0
        
        # Check and consume requirements (inputs)
        for req_resource_id, req_amount_per_unit in source.requirements.items():
            total_required = req_amount_per_unit * amount
            if not inventory.has_resource(req_resource_id, total_required):
                return 0.0
            inventory.remove_resource(req_resource_id, total_required)
        
        # Produce the resource (add to inventory)
        inventory.add_resource(resource_id, amount)
        
        return amount
    
    def _fulfill_from_world_fallback(
        self,
        entity: Entity,
        resource_id: str,
        amount: float,
        world_state: WorldState
    ) -> RequirementResolution:
        """Fallback: Consume directly from world resource pool.
        
        This is a Phase 2 fallback when no sources are configured.
        In later phases, proper sources (inventory, market, etc.) should be configured.
        
        Args:
            entity: Entity requesting fulfillment
            resource_id: Resource identifier
            amount: Required amount
            world_state: World state for context
            
        Returns:
            RequirementResolution with success status
        """
        global_resource = world_state.get_resource(resource_id)
        if global_resource is None:
            return RequirementResolution(
                success=False,
                source_id='world_fallback',
                amount_fulfilled=0.0,
                amount_requested=amount,
                reason=f"Resource {resource_id} does not exist in world"
            )
        
        # Try to consume the requested amount
        if global_resource.current_amount >= amount:
            global_resource.consume(amount)
            return RequirementResolution(
                success=True,
                source_id='world_fallback',
                amount_fulfilled=amount,
                amount_requested=amount
            )
        
        # Try to fulfill as much as possible
        available = global_resource.current_amount
        if available > 0:
            global_resource.consume(available)
            return RequirementResolution(
                success=True,
                source_id='world_fallback',
                amount_fulfilled=available,
                amount_requested=amount
            )
        
        # No resource available
        return RequirementResolution(
            success=False,
            source_id='world_fallback',
            amount_fulfilled=0.0,
            amount_requested=amount,
            reason=f"Insufficient {resource_id} in world (available: {available}, requested: {amount})"
        )
