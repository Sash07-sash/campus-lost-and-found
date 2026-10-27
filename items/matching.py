import re
from datetime import timedelta
from typing import List, Dict, Any
from .models import Item

# Common English stopwords to ignore when extracting keywords
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
    'with', 'by', 'from', 'up', 'about', 'into', 'over', 'after', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
    'did', 'i', 'me', 'my', 'myself', 'we', 'our', 'you', 'your', 'he', 'him',
    'his', 'she', 'her', 'it', 'its', 'they', 'them', 'their', 'this', 'that',
    'these', 'those', 'am', 'lost', 'found', 'please', 'help', 'item', 'campus',
    'here', 'there', 'near', 'some', 'any', 'very', 'just', 'can', 'could'
}


def extract_keywords(text: str) -> set:
    """Extract clean keyword tokens from title and description."""
    if not text:
        return set()
    words = re.findall(r'[a-zA-Z0-9]+', text.lower())
    return {w for w in words if len(w) > 2 and w not in STOP_WORDS}


def calculate_match_score(target_item: Item, candidate: Item) -> Dict[str, Any]:
    """
    Calculate match score (0 - 100) between a target item and a candidate item.
    Weights:
      - Keywords similarity (Title & Description): up to 40 points
      - Category match: 25 points
      - Campus location match: 20 points
      - Date compatibility: up to 15 points
    """
    total_score = 0.0
    reasons = []

    # 1. Category Matching (Weight: 25%)
    if target_item.category == candidate.category:
        total_score += 25.0
        reasons.append("Identical item category (+25%)")

    # 2. Campus Location Matching (Weight: 20%)
    target_loc = target_item.campus_location.strip().lower()
    cand_loc = candidate.campus_location.strip().lower()
    if target_loc == cand_loc:
        total_score += 20.0
        reasons.append(f"Exact location match: {candidate.campus_location} (+20%)")
    elif target_loc in cand_loc or cand_loc in target_loc:
        total_score += 12.0
        reasons.append("Close campus vicinity match (+12%)")

    # 3. Keyword Overlap (Title & Description) (Weight: 40%)
    # Give higher weight to title words
    target_title_kw = extract_keywords(target_item.title)
    cand_title_kw = extract_keywords(candidate.title)
    target_all_kw = target_title_kw | extract_keywords(target_item.description)
    cand_all_kw = cand_title_kw | extract_keywords(candidate.description)

    title_overlap = target_title_kw & cand_title_kw
    all_overlap = target_all_kw & cand_all_kw

    keyword_score = 0.0
    if title_overlap:
        # Direct title keyword match is strong
        ratio = len(title_overlap) / max(len(target_title_kw), 1)
        keyword_score += min(ratio * 25.0, 25.0)
        reasons.append(f"Title keywords matched: {', '.join(sorted(title_overlap)[:3])}")

    if all_overlap:
        # Description / general keyword overlap
        ratio = len(all_overlap) / max(len(target_all_kw | cand_all_kw), 1)
        keyword_score += min(ratio * 30.0, 15.0)

    keyword_score = min(keyword_score, 40.0)
    total_score += keyword_score
    if keyword_score > 0 and not title_overlap:
        reasons.append(f"Description keywords matched: {', '.join(sorted(all_overlap)[:3])}")

    # 4. Date Proximity & Logic (Weight: 15%)
    # If target is LOST: candidate FOUND should be on or after lost date (or up to 1 day before due to reporting time)
    # If target is FOUND: candidate LOST should be on or before found date
    date_score = 0.0
    day_diff = (candidate.date_lost_or_found - target_item.date_lost_or_found).days

    if target_item.report_type == 'LOST':
        # Candidate is FOUND
        if day_diff >= -1 and day_diff <= 14:
            # Found around the time or up to 2 weeks after
            if 0 <= day_diff <= 2:
                date_score = 15.0
                reasons.append(f"Date match: Found within {day_diff} day(s) of being lost (+15%)")
            elif day_diff <= 7:
                date_score = 10.0
                reasons.append("Date match: Found within 1 week of loss (+10%)")
            else:
                date_score = 5.0
                reasons.append("Date match: Found within 2 weeks of loss (+5%)")
    else:
        # Target is FOUND, Candidate is LOST
        # day_diff = candidate.lost_date - target.found_date
        # Candidate lost date should be <= target found date (day_diff <= 1)
        inv_diff = -day_diff
        if inv_diff >= -1 and inv_diff <= 14:
            if 0 <= inv_diff <= 2:
                date_score = 15.0
                reasons.append(f"Date match: Lost within {inv_diff} day(s) of recovery (+15%)")
            elif inv_diff <= 7:
                date_score = 10.0
                reasons.append("Date match: Lost within 1 week (+10%)")
            else:
                date_score = 5.0
                reasons.append("Date match: Lost within 2 weeks (+5%)")

    total_score += date_score

    # Determine confidence level label
    rounded_score = round(total_score)
    if rounded_score >= 65:
        confidence = "High Match"
        confidence_class = "success"
    elif rounded_score >= 40:
        confidence = "Moderate Match"
        confidence_class = "primary"
    else:
        confidence = "Potential Match"
        confidence_class = "warning text-dark"

    return {
        'candidate': candidate,
        'score': min(rounded_score, 100),
        'reasons': reasons,
        'confidence': confidence,
        'confidence_class': confidence_class,
    }


def find_possible_matches(target_item: Item, limit: int = 5, min_threshold: int = 25) -> List[Dict[str, Any]]:
    """
    Find potentially matching listings for target_item.
    - If target_item is LOST, search active FOUND items.
    - If target_item is FOUND, search active LOST items.
    - Excludes target_item, recovered items, and items with score < min_threshold.
    """
    opposite_type = 'FOUND' if target_item.report_type == 'LOST' else 'LOST'

    # Filter candidates: opposite report type, active (OPEN or CLAIM_PENDING), not recovered
    candidates = (
        Item.objects.filter(
            report_type=opposite_type,
            status__in=['OPEN', 'CLAIM_PENDING'],
            is_flagged=False
        )
        .exclude(pk=target_item.pk)
    )

    scored_matches = []
    for cand in candidates:
        match_info = calculate_match_score(target_item, cand)
        if match_info['score'] >= min_threshold:
            scored_matches.append(match_info)

    # Sort descending by score, then newest
    scored_matches.sort(key=lambda m: (m['score'], m['candidate'].created_at), reverse=True)
    return scored_matches[:limit]
