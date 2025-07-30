"""Main entry point - provides instructions for running Chainlit."""

def main():
    """Print instructions for running the Chainlit app."""
    print("To run the Long-Term Memory chatbot:")
    print()
    print("1. Set your API key:")
    print("   export ANTHROPIC_API_KEY='your-key-here'")
    print()
    print("2. Run the Chainlit app:")
    print("   chainlit run -m simple_ltm.app")
    print()
    print("3. Open http://localhost:8000 in your browser")
    print()
    print("For development with auto-reload:")
    print("   chainlit run -m simple_ltm.app -w")

if __name__ == "__main__":
    main()