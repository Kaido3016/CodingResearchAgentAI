"""CLI entry point for the evidence-aware developer tools research agent."""
import logging

from dotenv import load_dotenv
from src.workflow import Workflow

load_dotenv()
logging.basicConfig(level="INFO", format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    workflow = Workflow()
    print("Developer Tools Research Agent (type 'quit' or 'exit' to stop)")
    while True:
        try:
            query = input("\n🔍 Developer Tools Query: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye")
            break
        if query.casefold() in {"quit", "exit"}:
            break
        if not query:
            continue
        try:
            result = workflow.run(query)
        except Exception:
            logger.exception("Research run failed")
            print("Research failed. Check the configuration and logs, then try again.")
            continue

        print(f"\n📊 Results for: {query}\n{'=' * 60}")
        for index, company in enumerate(result.companies, 1):
            print(f"\n{index}. {company.name} [{company.research_status}]")
            print(f"   Website/source: {company.website or 'Not available'}")
            print(f"   Pricing: {company.pricing_model or 'Unknown'}")
            print(f"   Open source: {company.is_open_source if company.is_open_source is not None else 'Unknown'}")
            print(f"   API availability: {company.api_available if company.api_available is not None else 'Unknown'}")
            if company.description:
                print(f"   Description: {company.description}")
            if company.tech_stack:
                print(f"   Tech stack: {', '.join(company.tech_stack[:5])}")
            if company.language_support:
                print(f"   Languages: {', '.join(company.language_support[:5])}")
            if company.integration_capabilities:
                print(f"   Integrations: {', '.join(company.integration_capabilities[:4])}")
            if company.evidence:
                print("   Evidence:")
                for evidence in company.evidence[:5]:
                    print(f"     - {evidence.field}: {evidence.value} — {evidence.source_url}")
                    if evidence.excerpt:
                        print(f"       “{evidence.excerpt}”")
            else:
                print("   Evidence: no verifiable excerpts were returned; treat attributes as unverified.")
        if result.errors:
            print("\nResearch warnings:")
            for error in result.errors:
                print(f" - {error}")
        if result.analysis:
            print("\nDeveloper recommendation\n" + "-" * 40)
            print(result.analysis)


if __name__ == "__main__":
    main()
