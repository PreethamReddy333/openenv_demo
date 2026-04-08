"""FastAPI server for the Compliance Checker environment.

This file is at server/app.py (project root level) and imports from the
compliance_checker package which must be on PYTHONPATH.
"""

import uvicorn
from openenv.core.env_server import create_fastapi_app
from compliance_checker.models import ComplianceAction, ComplianceObservation
from compliance_checker.server.environment import ComplianceEnvironment

app = create_fastapi_app(ComplianceEnvironment, ComplianceAction, ComplianceObservation)


def main():
    """Entry point for the server."""
    uvicorn.run(
        "server.app:app",
        host="0.0.0.0",
        port=7860,
        reload=False,
    )


if __name__ == "__main__":
    main()
