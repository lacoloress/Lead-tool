"""Company analysis and scoring service."""

from lead_tool.models import Analysis, Category, Tier


class CompanyAnalyzer:
    """Analyzes companies and assigns scores based on criteria."""

    # Industries that get bonus points
    TARGET_INDUSTRIES = {"saas", "software", "technology", "internet"}

    # Size ranges and their scores
    MID_SIZES = {"51-200", "201-500", "501-1000"}
    ENTERPRISE_SIZES = {"1001-5000", "5001-10000", "10001+"}

    def analyze(
        self,
        industry: str = "",
        size: str = "",
        revenue: str = "",
    ) -> Analysis:
        """
        Analyze a company and return scoring results.

        Scoring criteria:
        - Industry (SaaS/Software/Tech/Internet): +30
        - Company Size (51-1000): +25
        - Company Size (1001+): +40
        - Revenue (Millions): +20
        - Revenue (Billions): +35
        """
        score = 0
        insights: list[str] = []

        # Industry scoring
        industry_lower = industry.lower()
        if any(target in industry_lower for target in self.TARGET_INDUSTRIES):
            score += 30
            insights.append(f"Target industry: {industry.title()} (+30)")

        # Size scoring
        if size in self.MID_SIZES:
            score += 25
            insights.append(f"Mid-market size: {size} (+25)")
        elif size in self.ENTERPRISE_SIZES:
            score += 40
            insights.append(f"Enterprise size: {size} (+40)")

        # Revenue scoring
        revenue_lower = revenue.lower()
        if any(x in revenue_lower for x in ["b", "billion"]):
            score += 35
            insights.append("Billion-dollar revenue (+35)")
        elif any(x in revenue_lower for x in ["m", "million"]):
            score += 20
            insights.append("Million-dollar revenue (+20)")

        # Cap score at 100
        score = min(score, 100)

        # Determine tier and category
        tier, category = self._classify(score)

        return Analysis(
            score=score,
            tier=tier,
            category=category,
            insights=insights,
            qualified=score >= 50,
        )

    def _classify(self, score: int) -> tuple[Tier, Category]:
        """Classify based on score."""
        if score >= 80:
            return Tier.ENTERPRISE, Category.HIGH_VALUE
        if score >= 60:
            return Tier.SCALE_UP, Category.MEDIUM_VALUE
        if score >= 40:
            return Tier.STARTUP, Category.STARTUP
        return Tier.SMALL, Category.SMALL_BUSINESS
