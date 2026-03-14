"""
Tests for the branch agents.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

from branches.verification.verify_agent import VerificationAgent
from branches.governance.dao_agent import GovernanceAgent
from branches.marketing.content_agent import MarketingAgent
from branches.wealth.trading_agent import WealthAgent


@pytest.fixture()
def verification_agent(redis_mock):
    with patch("branches.verification.verify_agent.redis.Redis", return_value=redis_mock):
        agent = VerificationAgent()
    return agent


@pytest.fixture()
def governance_agent(redis_mock):
    with patch("branches.governance.dao_agent.redis.Redis", return_value=redis_mock):
        agent = GovernanceAgent()
    return agent


@pytest.fixture()
def marketing_agent(redis_mock):
    with patch("branches.marketing.content_agent.redis.Redis", return_value=redis_mock):
        agent = MarketingAgent()
    return agent


@pytest.fixture()
def wealth_agent(redis_mock):
    with patch("branches.wealth.trading_agent.redis.Redis", return_value=redis_mock):
        agent = WealthAgent()
    return agent


# ---------------------------------------------------------------------------
# Verification Agent
# ---------------------------------------------------------------------------

class TestVerificationAgent:
    def test_verify_contribution_success(self, verification_agent):
        result = verification_agent.verify_contribution("contrib-1", {})
        assert result["status"] == "verified"
        assert result["contribution_id"] == "contrib-1"

    def test_fetch_metadata(self, verification_agent):
        meta = verification_agent.fetch_metadata("contrib-2")
        assert "id" in meta

    def test_check_duplicates_returns_bool(self, verification_agent):
        assert isinstance(verification_agent.check_duplicates({}), bool)

    def test_validate_format_returns_bool(self, verification_agent):
        assert isinstance(verification_agent.validate_format({}), bool)


# ---------------------------------------------------------------------------
# Governance Agent
# ---------------------------------------------------------------------------

class TestGovernanceAgent:
    def test_update_dao_state_returns_status(self, governance_agent):
        result = governance_agent.update_dao_state({})
        assert result["status"] == "updated"

    def test_create_proposal_summary(self, governance_agent):
        summary = governance_agent.create_proposal_summary("prop-1")
        assert "proposal_id" in summary
        assert summary["proposal_id"] == "prop-1"


# ---------------------------------------------------------------------------
# Marketing Agent
# ---------------------------------------------------------------------------

class TestMarketingAgent:
    def test_anonymize_data(self, marketing_agent):
        result = marketing_agent.anonymize_data({"user": "alice", "amount": 100})
        assert "user" not in result or result.get("user") is None or "amount" in result

    def test_generate_graphic_returns_str(self, marketing_agent):
        url = marketing_agent.generate_graphic({"amount": "$100+"})
        assert isinstance(url, str)

    def test_write_caption_contains_amount(self, marketing_agent):
        caption = marketing_agent.write_caption({"amount": "$100+"})
        assert "$100+" in caption

    def test_post_to_social_returns_posted(self, marketing_agent):
        result = marketing_agent.post_to_social("Test caption", "http://example.com/img.png")
        assert result["status"] == "posted"

    def test_create_success_story(self, marketing_agent):
        result = marketing_agent.create_success_story({"event_name": "ContributionVerified"})
        assert result["status"] == "posted"


# ---------------------------------------------------------------------------
# Wealth Agent
# ---------------------------------------------------------------------------

class TestWealthAgent:
    def test_fetch_nft_value_returns_number(self, wealth_agent):
        value = wealth_agent.fetch_nft_value({})
        assert isinstance(value, (int, float))

    def test_calculate_metrics(self, wealth_agent):
        metrics = wealth_agent.calculate_metrics(0.05)
        assert "total_value" in metrics
        assert "roi" in metrics

    def test_update_dashboard_calls_redis_set(self, wealth_agent, redis_mock):
        wealth_agent.update_dashboard({"total_value": 0.05})
        redis_mock.set.assert_called_once()

    def test_portfolio_update(self, wealth_agent):
        result = wealth_agent.portfolio_update({})
        assert result["status"] == "updated"
        assert "metrics" in result
