"""Job system for human employment.

Handles job assignment, resource production, salary payment, and employment management.
Jobs can produce resources or just pay money. Employment limits are dynamic based on population.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.core.system import System
from src.core.logging import get_logger
from src.models.components.employment import EmploymentComponent
from src.models.components.skills import SkillsComponent
from src.models.components.age import AgeComponent
from src.models.components.wealth import WealthComponent


logger = get_logger('systems.human.job')


def _should_run_on_frequency(frequency: str, current_datetime: datetime) -> bool:
    """Check if system should run based on frequency.
    
    Args:
        frequency: 'hourly', 'daily', 'weekly', 'monthly', or 'yearly'
        current_datetime: Current simulation datetime
        
    Returns:
        True if system should run this tick
    """
    if frequency == 'hourly':
        return True
    
    if frequency == 'daily':
        return current_datetime.hour == 0
    
    if frequency == 'weekly':
        return current_datetime.weekday() == 0 and current_datetime.hour == 0
    
    if frequency == 'monthly':
        return current_datetime.day == 1 and current_datetime.hour == 0
    
    if frequency == 'yearly':
        return (current_datetime.month == 1 and 
                current_datetime.day == 1 and 
                current_datetime.hour == 0)
    
    return False


class JobSystem(System):
    """System that manages human employment, job assignment, and resource production.
    
    Features:
    - Skills-based job assignment with charisma effects
    - Dynamic employment limits based on population percentage
    - Resource production from jobs
    - Salary payment and increases
    - Job loss (firing, quitting, layoffs)
    """
    
    @property
    def system_id(self) -> str:
        """Get system identifier."""
        return "JobSystem"
    
    def __init__(self):
        """Initialize the job system."""
        self.enabled: bool = True
        self.assignment_frequency: str = 'monthly'
        self.production_frequency: str = 'monthly'  # Default production frequency
        
        # Job definitions: job_id -> job_config
        self.jobs: Dict[str, Dict[str, Any]] = {}
        
        # Global settings
        self.min_work_age: int = 15
        self.max_work_age: int = 70
        self.base_hiring_chance: float = 0.3
        self.hiring_chance_multiplier: float = 0.5
        
        # Salary increase settings
        self.yearly_raise_probability: float = 0.7
        self.six_month_raise_probability: float = 0.05
        self.raise_amount_range: List[float] = [0.02, 0.05]  # 2-5% increase
        
        # Job loss settings (hardcoded for now)
        self.job_loss_probability: float = 0.01  # 1% chance per month
        
        # Track last assignment month to avoid duplicate assignments
        self.last_assignment_month: Optional[Tuple[int, int]] = None  # (year, month)
    
    def init(self, world_state: Any, config: Dict[str, Any]) -> None:
        """Initialize the system with configuration.
        
        Args:
            world_state: World state instance
            config: System configuration containing job definitions and settings
        """
        self.enabled = config.get('enabled', True)
        self.assignment_frequency = config.get('assignment_frequency', 'monthly')
        self.production_frequency = config.get('production_frequency', 'monthly')
        
        # Load job definitions
        jobs_config = config.get('jobs', {})
        for job_id, job_config in jobs_config.items():
            self.jobs[job_id] = self._parse_job_config(job_id, job_config)
        
        # Global age restrictions
        self.min_work_age = config.get('min_work_age', 15)
        self.max_work_age = config.get('max_work_age', 70)
        
        # Hiring settings
        self.base_hiring_chance = config.get('base_hiring_chance', 0.3)
        self.hiring_chance_multiplier = config.get('hiring_chance_multiplier', 0.5)
        
        # Salary increase settings
        self.yearly_raise_probability = config.get('yearly_raise_probability', 0.7)
        self.six_month_raise_probability = config.get('six_month_raise_probability', 0.05)
        self.raise_amount_range = config.get('raise_amount_range', [0.02, 0.05])
        
        # Job loss is hardcoded for now (documented for future configurability)
        # NOTE: Job loss probability is hardcoded. Future: Make configurable per job type
        # and differentiate between firing/quitting/layoffs
        
        logger.debug(
            f"Initialized {self.system_id}: enabled={self.enabled}, "
            f"jobs={len(self.jobs)}, assignment_frequency={self.assignment_frequency}"
        )
    
    def _parse_job_config(self, job_id: str, job_config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate a job configuration.
        
        Args:
            job_id: Job identifier
            job_config: Job configuration dictionary
            
        Returns:
            Parsed and validated job configuration
        """
        parsed = {
            'id': job_id,
            'name': job_config.get('name', job_id),
            'max_percentage': float(job_config.get('max_percentage', 10.0)),
            'max_salary': float(job_config.get('max_salary', 100.0)),
            'max_salary_cap': float(job_config.get('max_salary_cap', job_config.get('max_salary', 100.0) * 1.3)),
            'min_salary': float(job_config.get('min_salary', 50.0)),
            'min_age': int(job_config.get('min_age', self.min_work_age)),
            'required_skill': job_config.get('required_skill', 'general'),
            'skill_weight': float(job_config.get('skill_weight', 0.5)),
            'charisma_weight': float(job_config.get('charisma_weight', 0.1)),
            'job_type': job_config.get('job_type', 'production'),  # production or service
            'prioritize_unemployed': job_config.get('prioritize_unemployed', False),
        }
        
        # Production config (optional - service jobs don't produce)
        if 'production' in job_config:
            prod_config = job_config['production']
            parsed['production'] = {
                'resource_id': prod_config.get('resource_id'),
                'rate': float(prod_config.get('rate', 0.0)),
                'frequency': prod_config.get('frequency', self.production_frequency)
            }
        else:
            parsed['production'] = None
        
        return parsed
    
    def on_tick(self, world_state: Any, current_datetime: datetime) -> None:
        """Process a simulation tick.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        if not self.enabled:
            return
        
        # Job assignment (monthly)
        if _should_run_on_frequency(self.assignment_frequency, current_datetime):
            self._assign_jobs(world_state, current_datetime)
        
        # Resource production (configurable per job)
        self._produce_resources(world_state, current_datetime)
        
        # Pay salaries (when production happens or monthly for service jobs)
        self._pay_salaries(world_state, current_datetime)
        
        # Salary reviews (yearly on hire anniversary + rare 6-month)
        self._review_salaries(world_state, current_datetime)
        
        # Job loss checks (monthly)
        if _should_run_on_frequency('monthly', current_datetime):
            self._check_job_loss(world_state, current_datetime)
    
    def _assign_jobs(self, world_state: Any, current_datetime: datetime) -> None:
        """Assign jobs to unemployed humans.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        # Avoid duplicate assignments in the same month
        current_month = (current_datetime.year, current_datetime.month)
        if self.last_assignment_month == current_month:
            return
        self.last_assignment_month = current_month
        
        # Get all entities with Age component (to check work eligibility)
        all_entities = world_state.get_all_entities()
        eligible_entities = []
        
        for entity in all_entities.values():
            age_comp = entity.get_component('Age')
            if not age_comp:
                continue
            
            age_years = age_comp.get_age_years(current_datetime)
            
            # Check global age restrictions
            if age_years < self.min_work_age or age_years > self.max_work_age:
                continue
            
            # Check if already employed
            employment = entity.get_component('Employment')
            if employment and employment.is_employed():
                continue
            
            eligible_entities.append(entity)
        
        if not eligible_entities:
            return
        
        # For each job type, try to fill open positions
        for job_id, job_config in self.jobs.items():
            self._fill_job_positions(world_state, current_datetime, job_id, job_config, eligible_entities)
    
    def _fill_job_positions(
        self,
        world_state: Any,
        current_datetime: datetime,
        job_id: str,
        job_config: Dict[str, Any],
        eligible_entities: List[Any]
    ) -> None:
        """Fill open positions for a specific job type.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
            job_id: Job identifier
            job_config: Job configuration
            eligible_entities: List of eligible entities (unemployed, right age)
        """
        # Calculate max workers based on population percentage
        total_population = len(world_state.get_all_entities())
        max_workers = int((total_population * job_config['max_percentage']) / 100.0)
        
        # Count current workers
        current_workers = self._count_workers(world_state, job_id)
        
        # Check if job is full
        if current_workers >= max_workers:
            # Log if job just became full (first time we see it full)
            # TODO: Track previous state to detect transitions
            return
        
        open_slots = max_workers - current_workers
        
        # Calculate fill percentage for dynamic hiring chance
        fill_percentage = current_workers / max_workers if max_workers > 0 else 0.0
        
        # Adjust hiring chance based on fill percentage
        # Empty jobs are "needy" (higher chance), full jobs are "picky" (lower chance)
        adjusted_chance = self.base_hiring_chance * (1.0 + (1.0 - fill_percentage) * self.hiring_chance_multiplier)
        adjusted_chance = min(1.0, adjusted_chance)  # Cap at 100%
        
        # Filter entities by job-specific age requirement
        job_min_age = job_config.get('min_age', self.min_work_age)
        candidates = []
        
        for entity in eligible_entities:
            age_comp = entity.get_component('Age')
            if not age_comp:
                continue
            
            age_years = age_comp.get_age_years(current_datetime)
            if age_years < job_min_age:
                continue
            
            candidates.append(entity)
        
        # Sort candidates by suitability (for now, random - will enhance with skills)
        # Shuffle to avoid always picking the same entities
        import random
        random.shuffle(candidates)
        
        # Try to hire candidates
        hired_count = 0
        for entity in candidates:
            if hired_count >= open_slots:
                break
            
            # Check if entity should be hired (probabilistic)
            if world_state.rng.random() > adjusted_chance:
                continue
            
            # Calculate hiring probability based on skills and charisma
            if self._should_hire_entity(world_state, entity, job_config):
                self._hire_entity(world_state, current_datetime, entity, job_id, job_config)
                hired_count += 1
        
        # Log job full/opening status
        new_workers = self._count_workers(world_state, job_id)
        if new_workers >= max_workers and current_workers < max_workers:
            logger.info(f"Job '{job_config['name']}' ({job_id}) is now FULL ({new_workers}/{max_workers} workers)")
        elif new_workers < max_workers and current_workers >= max_workers:
            logger.info(f"Job '{job_config['name']}' ({job_id}) has OPENINGS ({new_workers}/{max_workers} workers, {max_workers - new_workers} slots open)")
    
    def _should_hire_entity(
        self,
        world_state: Any,
        entity: Any,
        job_config: Dict[str, Any]
    ) -> bool:
        """Determine if an entity should be hired for a job.
        
        Args:
            world_state: World state instance
            entity: Entity to evaluate
            job_config: Job configuration
            
        Returns:
            True if entity should be hired
        """
        skills = entity.get_component('Skills')
        if not skills:
            # No skills component - use base probability
            return world_state.rng.random() < 0.5
        
        # Get required skill value
        required_skill = job_config['required_skill']
        skill_value = skills.get_job_skill(required_skill, 0.0)
        charisma = skills.charisma
        
        # Calculate hiring score
        skill_score = skill_value * job_config['skill_weight']
        charisma_score = charisma * job_config['charisma_weight']
        total_score = skill_score + charisma_score
        
        # Normalize to 0-1 range (assuming max possible is skill_weight + charisma_weight)
        max_possible = job_config['skill_weight'] + job_config['charisma_weight']
        if max_possible > 0:
            normalized_score = total_score / max_possible
        else:
            normalized_score = 0.5
        
        # Use score as probability (higher score = more likely to hire)
        return world_state.rng.random() < normalized_score
    
    def _hire_entity(
        self,
        world_state: Any,
        current_datetime: datetime,
        entity: Any,
        job_id: str,
        job_config: Dict[str, Any]
    ) -> None:
        """Hire an entity for a job.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
            entity: Entity to hire
            job_id: Job identifier
            job_config: Job configuration
        """
        # Calculate salary based on skills and charisma
        skills = entity.get_component('Skills')
        base_salary = world_state.rng.uniform(job_config['min_salary'], job_config['max_salary'])
        
        if skills:
            # Adjust salary based on skills match
            required_skill = job_config['required_skill']
            skill_value = skills.get_job_skill(required_skill, 0.0)
            charisma = skills.charisma
            
            # Skill bonus: up to 20% increase
            skill_bonus = skill_value * 0.2
            # Charisma bonus: up to 10% increase
            charisma_bonus = charisma * 0.1
            
            salary_multiplier = 1.0 + skill_bonus + charisma_bonus
            base_salary *= salary_multiplier
        
        # Cap at max_salary
        final_salary = min(base_salary, job_config['max_salary'])
        
        # Create or update employment component
        employment = entity.get_component('Employment')
        if not employment:
            employment = EmploymentComponent()
            entity.add_component(employment)
        
        employment.job_type = job_id
        employment.employer_id = None  # Self-employed for now
        employment.salary = final_salary
        employment.hire_date = current_datetime
        employment.last_raise_date = None
        employment.max_salary_cap = job_config['max_salary_cap']
        
        logger.info(
            f"Entity {entity.entity_id} hired as {job_config['name']} "
            f"(salary: {final_salary:.2f})"
        )
    
    def _count_workers(self, world_state: Any, job_id: str) -> int:
        """Count current workers for a job type.
        
        Args:
            world_state: World state instance
            job_id: Job identifier
            
        Returns:
            Number of workers with this job
        """
        count = 0
        for entity in world_state.get_all_entities().values():
            employment = entity.get_component('Employment')
            if employment and employment.job_type == job_id:
                count += 1
        return count
    
    def _produce_resources(self, world_state: Any, current_datetime: datetime) -> None:
        """Produce resources from jobs.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        for job_id, job_config in self.jobs.items():
            if not job_config.get('production'):
                continue  # Service jobs don't produce
            
            prod_config = job_config['production']
            frequency = prod_config.get('frequency', self.production_frequency)
            
            if not _should_run_on_frequency(frequency, current_datetime):
                continue
            
            # Count workers for this job
            worker_count = self._count_workers(world_state, job_id)
            if worker_count == 0:
                continue
            
            # Calculate production
            rate_per_worker = prod_config['rate']
            total_production = rate_per_worker * worker_count
            
            # Add to world resource
            resource_id = prod_config['resource_id']
            resource = world_state.get_resource(resource_id)
            if resource:
                added = resource.add(total_production)
                logger.debug(
                    f"Job '{job_config['name']}' produced {added:.2f} {resource_id} "
                    f"({worker_count} workers × {rate_per_worker:.2f} per worker)"
                )
    
    def _pay_salaries(self, world_state: Any, current_datetime: datetime) -> None:
        """Pay salaries to workers.
        
        Salaries are paid when production happens (for production jobs) or monthly (for service jobs).
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        # Get money resource
        money_resource = world_state.get_resource('money')
        if not money_resource:
            logger.warning("Money resource not found, cannot pay salaries")
            return
        
        # Pay salaries for all employed workers
        total_paid = 0.0
        paid_count = 0
        
        for entity in world_state.get_all_entities().values():
            employment = entity.get_component('Employment')
            if not employment or not employment.is_employed():
                continue
            
            # Check if this job should pay now
            job_config = self.jobs.get(employment.job_type)
            if not job_config:
                continue
            
            # Determine payment frequency
            if job_config.get('production'):
                # Production jobs pay when they produce
                prod_config = job_config['production']
                frequency = prod_config.get('frequency', self.production_frequency)
                if not _should_run_on_frequency(frequency, current_datetime):
                    continue
            else:
                # Service jobs pay monthly
                if not _should_run_on_frequency('monthly', current_datetime):
                    continue
            
            # Pay salary
            salary = employment.salary
            if salary > 0:
                # Check if world has enough money
                if money_resource.current_amount >= salary:
                    money_resource.consume(salary)
                    
                    # Add to entity's wealth
                    wealth = entity.get_component('Wealth')
                    if not wealth:
                        wealth = WealthComponent()
                        entity.add_component(wealth)
                    wealth.add_money(salary)
                    
                    total_paid += salary
                    paid_count += 1
                else:
                    logger.warning(
                        f"Insufficient world money to pay salary {salary:.2f} to entity {entity.entity_id}. "
                        f"World money: {money_resource.current_amount:.2f}"
                    )
        
        if paid_count > 0:
            logger.debug(
                f"Paid salaries to {paid_count} workers: total {total_paid:.2f} "
                f"(remaining world money: {money_resource.current_amount:.2f})"
            )
    
    def _review_salaries(self, world_state: Any, current_datetime: datetime) -> None:
        """Review and potentially increase salaries.
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        for entity in world_state.get_all_entities().values():
            employment = entity.get_component('Employment')
            if not employment or not employment.is_employed():
                continue
            
            if not employment.hire_date:
                continue
            
            # Check for yearly raise
            years_employed = (current_datetime - employment.hire_date).days / 365.25
            if years_employed >= 1.0:
                # Check if we've already given a raise this year
                if employment.last_raise_date:
                    years_since_raise = (current_datetime - employment.last_raise_date).days / 365.25
                    if years_since_raise < 1.0:
                        continue  # Already got raise this year
                
                # Yearly raise chance
                if world_state.rng.random() < self.yearly_raise_probability:
                    self._give_raise(world_state, entity, employment, current_datetime)
                    continue
            
            # Check for rare 6-month raise
            months_employed = (current_datetime - employment.hire_date).days / 30.0
            if months_employed >= 6.0:
                if employment.last_raise_date:
                    months_since_raise = (current_datetime - employment.last_raise_date).days / 30.0
                    if months_since_raise < 6.0:
                        continue
                
                # 6-month raise chance (rare)
                if world_state.rng.random() < self.six_month_raise_probability:
                    self._give_raise(world_state, entity, employment, current_datetime)
    
    def _give_raise(
        self,
        world_state: Any,
        entity: Any,
        employment: EmploymentComponent,
        current_datetime: datetime
    ) -> None:
        """Give a salary raise to an entity.
        
        Args:
            world_state: World state instance
            entity: Entity receiving raise
            employment: Employment component
            current_datetime: Current simulation datetime
        """
        if employment.salary >= employment.max_salary_cap:
            return  # Already at cap
        
        # Calculate raise amount (2-5% of current salary)
        raise_percent = world_state.rng.uniform(
            self.raise_amount_range[0],
            self.raise_amount_range[1]
        )
        raise_amount = employment.salary * raise_percent
        
        new_salary = min(employment.salary + raise_amount, employment.max_salary_cap)
        old_salary = employment.salary
        employment.salary = new_salary
        employment.last_raise_date = current_datetime
        
        logger.info(
            f"Entity {entity.entity_id} received salary raise: "
            f"{old_salary:.2f} → {new_salary:.2f} "
            f"(+{raise_amount:.2f}, {raise_percent*100:.1f}%)"
        )
    
    def _check_job_loss(self, world_state: Any, current_datetime: datetime) -> None:
        """Check for job loss (firing, quitting, layoffs).
        
        Args:
            world_state: World state instance
            current_datetime: Current simulation datetime
        """
        # NOTE: Job loss probability is hardcoded for now
        # Future: Make configurable per job type and differentiate between firing/quitting/layoffs
        
        entities_to_unemploy = []
        
        for entity in world_state.get_all_entities().values():
            employment = entity.get_component('Employment')
            if not employment or not employment.is_employed():
                continue
            
            # Small random chance of job loss
            if world_state.rng.random() < self.job_loss_probability:
                entities_to_unemploy.append((entity, employment))
        
        # Process job losses
        for entity, employment in entities_to_unemploy:
            job_id = employment.job_type
            job_config = self.jobs.get(job_id, {})
            job_name = job_config.get('name', job_id)
            
            # Remove employment
            employment.job_type = None
            employment.employer_id = None
            # Keep salary, hire_date, etc. for potential re-hiring reference
            
            logger.info(
                f"Entity {entity.entity_id} lost job '{job_name}' "
                f"(firing/quitting/layoff - not differentiated yet)"
            )
