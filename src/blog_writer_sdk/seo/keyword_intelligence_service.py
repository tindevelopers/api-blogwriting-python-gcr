"""
Keyword Intelligence Service

Centralizes keyword discovery and normalization across DataForSEO Labs,
Keywords Data, and SERP APIs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class KeywordIntelligenceService:
    """Aggregates keyword discovery signals into a normalized structure."""

    def __init__(self, dataforseo_client):
        self._df_client = dataforseo_client

    async def build_intelligence(
        self,
        seed_keyword: str,
        location_name: str,
        language_code: str,
        tenant_id: str,
        serp_depth: int = 10,
        include_matching_terms: bool = True,
        include_related_terms: bool = True,
        include_also_rank_for: bool = True,
        include_questions: bool = True,
        include_serp: bool = True,
        include_autocomplete: bool = True,
        include_suggestions: bool = True,
        include_keyword_ideas: bool = True,
        max_matching_terms: int = 200,
        max_related_terms: int = 200,
        max_suggestions: int = 150,
    ) -> Dict[str, Any]:
        """
        Return normalized keyword intelligence for a seed keyword.

        All output lists contain normalized keyword records with:
        keyword, search_volume, keyword_difficulty, cpc, competition, parent_topic, intent.
        """
        if not self._df_client:
            return {
                "seed_keyword": seed_keyword,
                "matching_terms": [],
                "related_terms": [],
                "suggested_terms": [],
                "autocomplete_terms": [],
                "questions": [],
                "also_rank_for": [],
                "also_talk_about": [],
                "serp_analysis": {},
            }

        await self._df_client.initialize_credentials(tenant_id)

        tasks = []
        task_names: List[str] = []

        if include_matching_terms:
            tasks.append(
                self._df_client.get_related_keywords(
                    keyword=seed_keyword,
                    location_name=location_name,
                    language_code=language_code,
                    tenant_id=tenant_id,
                    depth=2,
                    limit=max_matching_terms,
                )
            )
            task_names.append("related_keywords")

        if include_keyword_ideas:
            tasks.append(
                self._df_client.get_keyword_ideas(
                    keywords=[seed_keyword],
                    location_name=location_name,
                    language_code=language_code,
                    tenant_id=tenant_id,
                    limit=max_related_terms,
                )
            )
            task_names.append("keyword_ideas")

        if include_suggestions:
            tasks.append(
                self._df_client.get_keyword_suggestions(
                    seed_keyword=seed_keyword,
                    location_name=location_name,
                    language_code=language_code,
                    tenant_id=tenant_id,
                    limit=max_suggestions,
                )
            )
            task_names.append("keyword_suggestions")

        if include_autocomplete:
            tasks.append(
                self._df_client.get_autocomplete_suggestions(
                    keyword=seed_keyword,
                    location_name=location_name,
                    language_code=language_code,
                    tenant_id=tenant_id,
                    limit=min(100, max_suggestions),
                )
            )
            task_names.append("autocomplete")

        if include_also_rank_for:
            tasks.append(
                self._df_client.get_keyword_overview(
                    keywords=[seed_keyword],
                    location_name=location_name,
                    language_code=language_code,
                    tenant_id=tenant_id,
                )
            )
            task_names.append("keyword_overview")

        if include_serp:
            tasks.append(
                self._df_client.get_serp_analysis(
                    keyword=seed_keyword,
                    location_name=location_name,
                    language_code=language_code,
                    tenant_id=tenant_id,
                    depth=serp_depth,
                )
            )
            task_names.append("serp_analysis")

        results: Dict[str, Any] = {
            "seed_keyword": seed_keyword,
            "matching_terms": [],
            "related_terms": [],
            "suggested_terms": [],
            "autocomplete_terms": [],
            "questions": [],
            "also_rank_for": [],
            "also_talk_about": [],
            "serp_analysis": {},
        }

        if not tasks:
            return results

        task_results = await _gather_tasks(tasks)
        named_results = dict(zip(task_names, task_results))

        related_resp = named_results.get("related_keywords")
        if related_resp is not None:
            results["matching_terms"] = _extract_keywords_from_related_response(
                related_resp, limit=max_matching_terms
            )

        ideas_resp = named_results.get("keyword_ideas")
        if ideas_resp is not None:
            results["related_terms"] = _extract_keywords_from_ideas_response(
                ideas_resp, limit=max_related_terms
            )

        suggestions_resp = named_results.get("keyword_suggestions")
        if suggestions_resp is not None:
            results["suggested_terms"] = _extract_keywords_from_ideas_response(
                suggestions_resp, limit=max_suggestions
            )

        autocomplete_resp = named_results.get("autocomplete")
        if autocomplete_resp is not None:
            results["autocomplete_terms"] = _extract_keywords_from_autocomplete(
                autocomplete_resp, limit=min(100, max_suggestions)
            )

        overview_resp = named_results.get("keyword_overview")
        if overview_resp is not None:
            also_rank_for, also_talk_about = _extract_also_rank_for(overview_resp, seed_keyword)
            results["also_rank_for"] = also_rank_for
            results["also_talk_about"] = also_talk_about

        serp_resp = named_results.get("serp_analysis")
        if serp_resp is not None:
            results["serp_analysis"] = serp_resp if isinstance(serp_resp, dict) else {}

        if include_questions and results["matching_terms"]:
            results["questions"] = [
                term
                for term in results["matching_terms"]
                if _looks_like_question(term.get("keyword", ""))
            ][:50]

        return results


async def _gather_tasks(tasks: List[Any]) -> List[Any]:
    import asyncio

    try:
        return await asyncio.gather(*tasks, return_exceptions=True)
    except Exception as exc:
        logger.warning(f"Keyword intelligence tasks failed to start: {exc}")
        return [exc] * len(tasks)


def _extract_keywords_from_related_response(response: Any, limit: int = 200) -> List[Dict[str, Any]]:
    keywords: List[Dict[str, Any]] = []
    if not response:
        return keywords

    items = _extract_task_items(response)
    for item in items:
        normalized = _normalize_keyword_record(item)
        if normalized:
            keywords.append(normalized)
            if len(keywords) >= limit:
                break
    return keywords


def _extract_keywords_from_ideas_response(response: Any, limit: int = 200) -> List[Dict[str, Any]]:
    if not response:
        return []

    items = _extract_task_items(response)
    keywords: List[Dict[str, Any]] = []
    for item in items:
        normalized = _normalize_keyword_record(item)
        if normalized:
            keywords.append(normalized)
        if len(keywords) >= limit:
            break
    return keywords


def _extract_keywords_from_autocomplete(response: Any, limit: int = 100) -> List[Dict[str, Any]]:
    if not response:
        return []
    keywords: List[Dict[str, Any]] = []
    if isinstance(response, list):
        items = response
    else:
        items = _extract_task_items(response)
    for item in items:
        if isinstance(item, dict):
            keyword = item.get("keyword") or item.get("suggestion") or item.get("text")
        else:
            keyword = item if isinstance(item, str) else None
        if not keyword:
            continue
        keywords.append(
            {
                "keyword": keyword,
                "search_volume": 0,
                "keyword_difficulty": 0,
                "cpc": 0.0,
                "competition": 0.0,
                "parent_topic": None,
                "intent": None,
            }
        )
        if len(keywords) >= limit:
            break
    return keywords


def _extract_task_items(response: Any) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    if isinstance(response, dict) and "tasks" in response:
        for task in response.get("tasks", []):
            result_data = task.get("result")
            if result_data is None:
                continue
            if isinstance(result_data, list):
                for result in result_data:
                    if isinstance(result, dict):
                        items.extend(result.get("items", []))
            elif isinstance(result_data, dict):
                items.extend(result_data.get("items", []))
    elif isinstance(response, list):
        items = response
    return items


def _normalize_keyword_record(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(item, dict):
        return None

    keyword = item.get("keyword") or item.get("text")
    keyword_data = item.get("keyword_data", {})
    keyword_info = keyword_data.get("keyword_info", {})

    if not keyword:
        keyword = keyword_data.get("keyword")
    if not keyword:
        return None

    search_volume = keyword_info.get("search_volume", item.get("search_volume", 0))
    keyword_difficulty = keyword_info.get("keyword_difficulty", item.get("keyword_difficulty"))
    cpc = keyword_info.get("cpc", item.get("cpc", 0.0))
    competition = keyword_info.get("competition", item.get("competition", 0.0))

    intent_info = keyword_info.get("search_intent_info", keyword_data.get("search_intent_info", {}))
    intent = intent_info.get("main_intent") or keyword_info.get("search_intent") or item.get("search_intent")

    return {
        "keyword": keyword,
        "search_volume": search_volume or 0,
        "keyword_difficulty": keyword_difficulty or 0,
        "cpc": cpc or 0.0,
        "competition": competition or 0.0,
        "parent_topic": keyword_info.get("parent_topic"),
        "intent": intent,
    }


def _looks_like_question(keyword: str) -> bool:
    keyword_lower = keyword.lower()
    question_prefixes = ("how", "what", "when", "where", "why", "who", "can", "does", "is", "are", "should")
    return "?" in keyword or keyword_lower.startswith(question_prefixes)


def _extract_also_rank_for(response: Any, seed_keyword: str) -> tuple[List[str], List[str]]:
    items = _extract_task_items(response)
    target = None
    for item in items:
        if isinstance(item, dict) and item.get("keyword") == seed_keyword:
            target = item
            break
    if not target and items:
        target = items[0]

    also_rank_for = _extract_keyword_strings(target.get("also_rank_for", []) if target else [])
    also_talk_about = _extract_keyword_strings(target.get("also_talk_about", []) if target else [])
    return also_rank_for, also_talk_about


def _extract_keyword_strings(raw: Any, limit: int = 50) -> List[str]:
    results: List[str] = []
    if not raw:
        return results
    if not isinstance(raw, list):
        raw = [raw]
    for item in raw:
        if isinstance(item, dict):
            keyword = item.get("keyword") or item.get("text")
        else:
            keyword = item if isinstance(item, str) else None
        if keyword:
            results.append(keyword)
        if len(results) >= limit:
            break
    return results
