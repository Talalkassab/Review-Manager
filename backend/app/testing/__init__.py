"""
Agent Testing System
===================

Comprehensive testing framework for the Restaurant AI Agent System.
Provides interfaces for testing conversation flows, A/B testing,
scenario testing, performance monitoring, and integration testing.

Key Components:
- Test Conversation Playground with real-time analysis
- Customer Profile Simulator for generating test scenarios  
- A/B Testing Dashboard with statistical analysis
- Scenario Testing Framework with predefined test cases
- Agent Performance Monitor with real-time metrics
- Test Data Manager for synthetic data generation
- Integration testing utilities for WhatsApp and AI APIs
"""

from .conversation_playground import ConversationPlaygroundAPI
from .customer_simulator import CustomerProfileSimulator
from .ab_testing import ABTestingDashboard
from .scenario_testing import ScenarioTestingFramework
from .performance_monitor import AgentPerformanceMonitor
from .test_data_manager import TestDataManager
from .integration_tests import IntegrationTestingSuite

__all__ = [
    "ConversationPlaygroundAPI",
    "CustomerProfileSimulator", 
    "ABTestingDashboard",
    "ScenarioTestingFramework",
    "AgentPerformanceMonitor",
    "TestDataManager",
    "IntegrationTestingSuite"
]