"""
Trust Scoring Service (Phase 3)
Computes overall trust/confidence scores for policy update requests
"""

from typing import Dict, Optional
import logging
from config import config

logger = logging.getLogger(__name__)


class TrustScorer:
    """
    Service to compute trust scores for policy update requests
    
    Combines:
    - Claim detection confidence
    - Contradiction analysis confidence
    - Evidence strength
    - Optional: User reputation (future)
    """
    
    def __init__(self):
        """Initialize Trust Scorer"""
        self.enabled = config.ENABLE_POLICY_UNLEARNING
        
        # Load confidence thresholds from config
        self.threshold_low = config.POLICY_CLAIM_CONFIDENCE_LOW
        self.threshold_medium = config.POLICY_CLAIM_CONFIDENCE_MEDIUM
        self.threshold_high = config.POLICY_CLAIM_CONFIDENCE_HIGH
    
    def compute_trust_score(
        self,
        claim_confidence: float,
        contradiction_confidence: float,
        evidence_strength: str,
        user_history: Optional[Dict] = None
    ) -> Dict:
        """
        Compute overall trust score for policy update request
        
        Args:
            claim_confidence: Confidence from claim detection (0.0-1.0)
            contradiction_confidence: Confidence from contradiction analysis (0.0-1.0)
            evidence_strength: "weak", "moderate", or "strong"
            user_history: Optional user reputation data
            
        Returns:
            {
                "trust_score": float,  # 0.0 to 1.0
                "confidence_level": str,  # "low", "medium", "high"
                "requires_approval": bool,
                "reasoning": str,
                "score_breakdown": dict
            }
        """
        if not self.enabled:
            logger.info("Trust scoring disabled (feature flag off)")
            return {
                "trust_score": 0.0,
                "confidence_level": "low",
                "requires_approval": True,
                "reasoning": "Feature disabled",
                "score_breakdown": {}
            }
        
        # Evidence strength to numeric score
        evidence_score_map = {
            "weak": 0.3,
            "moderate": 0.6,
            "strong": 0.9
        }
        evidence_score = evidence_score_map.get(evidence_strength, 0.3)
        
        # User reputation score (future enhancement)
        user_reputation_score = self._compute_user_reputation(user_history) if user_history else 0.5
        
        # Weighted combination
        weights = {
            "claim_confidence": 0.30,
            "contradiction_confidence": 0.30,
            "evidence_strength": 0.30,
            "user_reputation": 0.10
        }
        
        trust_score = (
            claim_confidence * weights["claim_confidence"] +
            contradiction_confidence * weights["contradiction_confidence"] +
            evidence_score * weights["evidence_strength"] +
            user_reputation_score * weights["user_reputation"]
        )
        
        # Ensure score is in valid range
        trust_score = max(0.0, min(1.0, trust_score))
        
        # Determine confidence level
        if trust_score >= self.threshold_high:
            confidence_level = "high"
        elif trust_score >= self.threshold_medium:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Determine if approval is required
        requires_approval = self._requires_approval(trust_score, confidence_level)
        
        # Build reasoning
        reasoning = self._build_reasoning(
            trust_score,
            confidence_level,
            claim_confidence,
            contradiction_confidence,
            evidence_strength
        )
        
        # Score breakdown for transparency
        score_breakdown = {
            "claim_confidence": claim_confidence,
            "contradiction_confidence": contradiction_confidence,
            "evidence_score": evidence_score,
            "evidence_strength": evidence_strength,
            "user_reputation_score": user_reputation_score,
            "weights": weights,
            "final_score": trust_score
        }
        
        logger.info(f"Trust score computed: {trust_score:.2f} ({confidence_level})")
        
        return {
            "trust_score": trust_score,
            "confidence_level": confidence_level,
            "requires_approval": requires_approval,
            "reasoning": reasoning,
            "score_breakdown": score_breakdown
        }
    
    def _compute_user_reputation(self, user_history: Dict) -> float:
        """
        Compute user reputation score (future enhancement)
        
        Args:
            user_history: {
                "total_claims": int,
                "approved_claims": int,
                "rejected_claims": int,
                "account_age_days": int
            }
        
        Returns:
            Reputation score 0.0 to 1.0
        """
        # Placeholder implementation
        # Future: Consider approval rate, account age, role, etc.
        
        total_claims = user_history.get("total_claims", 0)
        approved_claims = user_history.get("approved_claims", 0)
        
        if total_claims == 0:
            return 0.5  # Neutral for new users
        
        approval_rate = approved_claims / total_claims
        
        # Simple reputation based on approval rate
        if approval_rate > 0.8:
            return 0.9
        elif approval_rate > 0.5:
            return 0.7
        elif approval_rate > 0.3:
            return 0.5
        else:
            return 0.3
    
    def _requires_approval(self, trust_score: float, confidence_level: str) -> bool:
        """
        Determine if human approval is required
        
        Currently: Always require approval (safety-first approach)
        Future: Could auto-approve very high confidence claims
        """
        # For Phase 3, always require approval per design document
        if config.POLICY_UPDATE_APPROVAL_REQUIRED:
            return True
        
        # Future: Could allow auto-approval for extremely high confidence
        # if trust_score >= 0.95 and confidence_level == "high":
        #     return False
        
        return True
    
    def _build_reasoning(
        self,
        trust_score: float,
        confidence_level: str,
        claim_confidence: float,
        contradiction_confidence: float,
        evidence_strength: str
    ) -> str:
        """Build human-readable reasoning for the trust score"""
        
        components = []
        
        # Claim confidence
        if claim_confidence >= 0.7:
            components.append(f"strong claim detection ({claim_confidence:.2f})")
        elif claim_confidence >= 0.5:
            components.append(f"moderate claim detection ({claim_confidence:.2f})")
        else:
            components.append(f"weak claim detection ({claim_confidence:.2f})")
        
        # Contradiction confidence
        if contradiction_confidence >= 0.7:
            components.append(f"clear contradiction found ({contradiction_confidence:.2f})")
        elif contradiction_confidence >= 0.5:
            components.append(f"possible contradiction ({contradiction_confidence:.2f})")
        else:
            components.append(f"minimal contradiction ({contradiction_confidence:.2f})")
        
        # Evidence strength
        components.append(f"{evidence_strength} evidence")
        
        reasoning = f"Trust score {trust_score:.2f} ({confidence_level}): " + ", ".join(components)
        
        return reasoning
    
    def classify_confidence_level(self, score: float) -> str:
        """
        Classify a score into confidence level
        
        Args:
            score: Trust score 0.0 to 1.0
            
        Returns:
            "low", "medium", or "high"
        """
        if score >= self.threshold_high:
            return "high"
        elif score >= self.threshold_medium:
            return "medium"
        else:
            return "low"


# Singleton instance
trust_scorer = TrustScorer()
