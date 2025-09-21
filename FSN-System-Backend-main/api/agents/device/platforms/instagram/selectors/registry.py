"""
Instagram Selector Registry
Multi-strategy selector engine with anchor-first priority and fallback tracking
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from ....drivers.base_driver import BaseDriver

logger = logging.getLogger(__name__)


@dataclass
class SelectorStrategy:
    """Individual selector strategy with metadata"""
    type: str
    value: str
    confidence: float
    notes: str = ""


@dataclass
class SelectorResult:
    """Result of selector execution"""
    element: Any
    strategy_used: SelectorStrategy
    execution_time_ms: int
    fallback_attempts: int


class SelectorEngine:
    """
    Multi-strategy selector engine with fallback tracking
    Implements anchor-first priority with telemetry
    """
    
    def __init__(self, driver: BaseDriver):
        self.driver = driver
        self.intents_cache: Dict[str, Dict] = {}
        self.fallback_stats: Dict[str, Dict[str, int]] = {}
        self.selectors_path = Path(__file__).parent / "intents"
    
    async def find_element_by_intent(
        self, 
        intent: str, 
        timeout: int = 10,
        context: str = None
    ) -> Optional[SelectorResult]:
        """
        Find element using intent-based multi-strategy approach
        Returns first successful match with strategy metadata
        """
        start_time = asyncio.get_event_loop().time()
        
        # Load intent definition
        intent_def = await self._load_intent(intent)
        if not intent_def:
            logger.error(f"Intent '{intent}' not found")
            return None
        
        strategies = intent_def.get("strategies", [])
        if not strategies:
            logger.error(f"No strategies defined for intent '{intent}'")
            return None
        
        # Sort strategies by confidence (highest first)
        strategies.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        
        fallback_attempts = 0
        
        for strategy_data in strategies:
            try:
                strategy = SelectorStrategy(
                    type=strategy_data["type"],
                    value=strategy_data["value"],
                    confidence=strategy_data.get("confidence", 0.5),
                    notes=strategy_data.get("notes", "")
                )
                
                logger.debug(f"Trying strategy for '{intent}': {strategy.type}={strategy.value}")
                
                element = await self._execute_strategy(strategy, timeout)
                if element:
                    execution_time_ms = int((asyncio.get_event_loop().time() - start_time) * 1000)
                    
                    # Record successful strategy
                    self._record_strategy_success(intent, strategy.type)
                    
                    logger.info(f"Found '{intent}' using {strategy.type} (confidence: {strategy.confidence})")
                    
                    return SelectorResult(
                        element=element,
                        strategy_used=strategy,
                        execution_time_ms=execution_time_ms,
                        fallback_attempts=fallback_attempts
                    )
                else:
                    fallback_attempts += 1
                    self._record_strategy_failure(intent, strategy.type)
                    
            except Exception as e:
                logger.debug(f"Strategy {strategy_data['type']} failed for '{intent}': {e}")
                fallback_attempts += 1
                self._record_strategy_failure(intent, strategy_data["type"])
                continue
        
        logger.warning(f"All strategies failed for intent '{intent}' after {fallback_attempts} attempts")
        return None
    
    async def find_sub_element(
        self,
        parent_element: Any,
        intent: str,
        sub_element_key: str,
        timeout: int = 5
    ) -> Optional[SelectorResult]:
        """Find sub-element within parent using intent definition"""
        intent_def = await self._load_intent(intent)
        if not intent_def:
            return None
        
        sub_elements = intent_def.get("sub_elements", {})
        sub_element_def = sub_elements.get(sub_element_key)
        
        if not sub_element_def:
            logger.warning(f"Sub-element '{sub_element_key}' not defined for intent '{intent}'")
            return None
        
        strategies = sub_element_def.get("strategies", [])
        strategies.sort(key=lambda s: s.get("confidence", 0), reverse=True)
        
        for strategy_data in strategies:
            try:
                strategy = SelectorStrategy(
                    type=strategy_data["type"],
                    value=strategy_data["value"],
                    confidence=strategy_data.get("confidence", 0.5)
                )
                
                # TODO: Implement sub-element finding within parent
                # This would search within the parent element scope
                element = await self._execute_strategy_in_parent(parent_element, strategy, timeout)
                
                if element:
                    self._record_strategy_success(f"{intent}.{sub_element_key}", strategy.type)
                    return SelectorResult(
                        element=element,
                        strategy_used=strategy,
                        execution_time_ms=0,  # TODO: Track timing
                        fallback_attempts=0
                    )
                    
            except Exception as e:
                logger.debug(f"Sub-element strategy failed: {e}")
                continue
        
        return None
    
    async def validate_element_state(
        self, 
        element: Any, 
        intent: str,
        expected_state: str = None
    ) -> bool:
        """Validate element matches intent expectations"""
        intent_def = await self._load_intent(intent)
        if not intent_def:
            return False
        
        validation = intent_def.get("validation", {})
        
        # Check required attributes
        required_attrs = validation.get("required_attributes", [])
        for attr in required_attrs:
            # TODO: Check element has required attributes
            pass
        
        # Check expected type
        expected_type = validation.get("expected_type")
        if expected_type:
            # TODO: Verify element type matches
            pass
        
        # State-specific validation (for like buttons, etc.)
        if expected_state and intent_def.get("state_detection"):
            return await self._validate_element_state(element, intent_def, expected_state)
        
        return True
    
    async def _execute_strategy(self, strategy: SelectorStrategy, timeout: int) -> Optional[Any]:
        """Execute individual selector strategy"""
        try:
            if strategy.type == "accessibility_id":
                return await self.driver.find_element("accessibility_id", strategy.value, timeout)
            elif strategy.type == "predicate":
                return await self.driver.find_element("predicate", strategy.value, timeout)
            elif strategy.type == "class_chain":
                return await self.driver.find_element("class_chain", strategy.value, timeout)
            elif strategy.type == "xpath":
                return await self.driver.find_element("xpath", strategy.value, timeout)
            elif strategy.type == "name":
                return await self.driver.find_element("name", strategy.value, timeout)
            elif strategy.type == "template_match":
                # TODO: Implement template matching
                logger.debug(f"Template matching not yet implemented: {strategy.value}")
                return None
            elif strategy.type == "relative":
                # TODO: Implement relative positioning
                logger.debug(f"Relative positioning not yet implemented")
                return None
            else:
                logger.warning(f"Unknown strategy type: {strategy.type}")
                return None
                
        except Exception as e:
            logger.debug(f"Strategy execution failed: {e}")
            return None
    
    async def _execute_strategy_in_parent(
        self, 
        parent: Any, 
        strategy: SelectorStrategy, 
        timeout: int
    ) -> Optional[Any]:
        """Execute strategy within parent element scope"""
        # TODO: Implement parent-scoped element finding
        # This would use the parent element as the search root
        return None
    
    async def _load_intent(self, intent: str) -> Optional[Dict]:
        """Load intent definition from JSON file"""
        if intent in self.intents_cache:
            return self.intents_cache[intent]
        
        intent_file = self.selectors_path / f"{intent}.json"
        if not intent_file.exists():
            logger.error(f"Intent file not found: {intent_file}")
            return None
        
        try:
            with open(intent_file, 'r') as f:
                intent_def = json.load(f)
                self.intents_cache[intent] = intent_def
                return intent_def
        except Exception as e:
            logger.error(f"Failed to load intent '{intent}': {e}")
            return None
    
    def _record_strategy_success(self, intent: str, strategy_type: str) -> None:
        """Record successful strategy usage for telemetry"""
        if intent not in self.fallback_stats:
            self.fallback_stats[intent] = {}
        
        if "success" not in self.fallback_stats[intent]:
            self.fallback_stats[intent]["success"] = {}
        
        strategy_key = f"success.{strategy_type}"
        if strategy_key not in self.fallback_stats[intent]:
            self.fallback_stats[intent][strategy_key] = 0
        
        self.fallback_stats[intent][strategy_key] += 1
    
    def _record_strategy_failure(self, intent: str, strategy_type: str) -> None:
        """Record failed strategy usage for telemetry"""
        if intent not in self.fallback_stats:
            self.fallback_stats[intent] = {}
        
        if "failure" not in self.fallback_stats[intent]:
            self.fallback_stats[intent]["failure"] = {}
        
        strategy_key = f"failure.{strategy_type}"
        if strategy_key not in self.fallback_stats[intent]:
            self.fallback_stats[intent][strategy_key] = 0
        
        self.fallback_stats[intent][strategy_key] += 1
    
    async def _validate_element_state(
        self, 
        element: Any, 
        intent_def: Dict, 
        expected_state: str
    ) -> bool:
        """Validate element is in expected state"""
        state_detection = intent_def.get("state_detection", {})
        state_def = state_detection.get(expected_state)
        
        if not state_def:
            return True  # No state validation defined
        
        # Check accessibility indicators
        accessibility_indicators = state_def.get("accessibility_indicators", [])
        for indicator in accessibility_indicators:
            # TODO: Check if element has accessibility indicator
            pass
        
        return True
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """Get fallback strategy usage statistics"""
        return {
            "intents_used": list(self.fallback_stats.keys()),
            "total_intents": len(self.fallback_stats),
            "stats_by_intent": self.fallback_stats,
            "top_successful_strategies": self._get_top_strategies("success"),
            "top_failed_strategies": self._get_top_strategies("failure")
        }
    
    def _get_top_strategies(self, result_type: str, limit: int = 5) -> List[Tuple[str, str, int]]:
        """Get top strategies by usage count"""
        strategy_counts = []
        
        for intent, stats in self.fallback_stats.items():
            type_stats = stats.get(result_type, {})
            for strategy_key, count in type_stats.items():
                strategy_type = strategy_key.replace(f"{result_type}.", "")
                strategy_counts.append((intent, strategy_type, count))
        
        # Sort by count descending
        strategy_counts.sort(key=lambda x: x[2], reverse=True)
        return strategy_counts[:limit]


class InstagramSelectorRegistry:
    """Registry for Instagram-specific selectors and utilities"""
    
    def __init__(self, driver: BaseDriver):
        self.driver = driver
        self.engine = SelectorEngine(driver)
    
    async def find_search_bar(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram search bar"""
        return await self.engine.find_element_by_intent("search", timeout)
    
    async def find_profile_header(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram profile header"""
        return await self.engine.find_element_by_intent("profile_header", timeout)
    
    async def find_post_card(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram post card"""
        return await self.engine.find_element_by_intent("post_card", timeout)
    
    async def find_actions_row(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram post actions row"""
        return await self.engine.find_element_by_intent("actions_row", timeout)
    
    async def find_like_button(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram like button with state detection"""
        return await self.engine.find_element_by_intent("like_button", timeout)
    
    async def find_home_tab(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram home tab"""
        return await self.engine.find_element_by_intent("home_tab", timeout)
    
    async def find_home_feed_container(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram home feed container"""
        return await self.engine.find_element_by_intent("main_feed_container", timeout)
    
    async def find_post_cell(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram post cell"""
        return await self.engine.find_element_by_intent("post_cell", timeout)
    
    async def find_like_button_home_feed(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram like button in home feed context"""
        return await self.engine.find_element_by_intent("like_button_home_feed", timeout)
    
    async def find_story_ring(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram story ring"""
        return await self.engine.find_element_by_intent("story_ring", timeout)
    
    async def find_stories_tray(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram stories tray"""
        return await self.engine.find_element_by_intent("stories_tray", timeout)
    
    async def find_story_dismiss_button(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram story dismiss button"""
        return await self.engine.find_element_by_intent("story_dismiss_button", timeout)
    
    async def find_back_button(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find Instagram back button"""
        return await self.engine.find_element_by_intent("back_button", timeout)
    
    async def find_follow_button(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find follow button on profile pages"""
        return await self.engine.find_element_by_intent("follow_button", timeout)
    
    async def find_following_button(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find following button on profile pages (indicates already following)"""
        return await self.engine.find_element_by_intent("following_button", timeout)
    
    async def find_requested_button(self, timeout: int = 10) -> Optional[SelectorResult]:
        """Find requested button on profile pages (follow request pending)"""
        return await self.engine.find_element_by_intent("requested_button", timeout)
    
    async def extract_profile_data(self, profile_header_element: Any) -> Dict[str, Any]:
        """Extract profile data from profile header element"""
        data = {}
        
        # Extract username
        username_result = await self.engine.find_sub_element(
            profile_header_element, "profile_header", "username"
        )
        if username_result:
            # TODO: Extract text from username element
            data["username"] = "extracted_username"
        
        # Extract follower count
        followers_result = await self.engine.find_sub_element(
            profile_header_element, "profile_header", "followers_count"
        )
        if followers_result:
            # TODO: Extract and parse follower count
            data["followers_count"] = 0
        
        # Extract following count
        following_result = await self.engine.find_sub_element(
            profile_header_element, "profile_header", "following_count"
        )
        if following_result:
            # TODO: Extract and parse following count
            data["following_count"] = 0
        
        # Extract posts count
        posts_result = await self.engine.find_sub_element(
            profile_header_element, "profile_header", "posts_count"
        )
        if posts_result:
            # TODO: Extract and parse posts count
            data["posts_count"] = 0
        
        # Extract bio
        bio_result = await self.engine.find_sub_element(
            profile_header_element, "profile_header", "bio"
        )
        if bio_result:
            # TODO: Extract bio text
            data["bio"] = "extracted_bio"
        
        return data
    
    def get_selector_telemetry(self) -> Dict[str, Any]:
        """Get comprehensive selector usage telemetry"""
        return {
            "engine_stats": self.engine.get_fallback_stats(),
            "cache_stats": {
                "cached_intents": len(self.engine.intents_cache),
                "intents_loaded": list(self.engine.intents_cache.keys())
            }
        }
