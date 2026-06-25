"""Marketing Page Quality Gate — deterministic landing-page scoring."""

from quality_gate.connectors import SUPPORTED_PLATFORMS, get_campaign_metrics
from quality_gate.cta import cta_clarity
from quality_gate.links import check_links, extract_links
from quality_gate.mobile import audit_mobile
from quality_gate.pixels import detect_pixels
from quality_gate.scoring import score_page

__all__ = [
    "SUPPORTED_PLATFORMS",
    "audit_mobile",
    "check_links",
    "cta_clarity",
    "detect_pixels",
    "extract_links",
    "get_campaign_metrics",
    "score_page",
]