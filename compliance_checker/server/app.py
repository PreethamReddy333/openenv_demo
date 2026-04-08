"""FastAPI server for the Compliance Checker environment."""

from openenv.core.env_server import create_fastapi_app
from compliance_checker.models import ComplianceAction, ComplianceObservation
from compliance_checker.server.environment import ComplianceEnvironment

app = create_fastapi_app(ComplianceEnvironment, ComplianceAction, ComplianceObservation)
