# Agent Message Examples

This document provides example JSON messages for agent-to-agent communication in Aegis.

## Message Schema

All messages follow the `AgentMessage` schema:

```json
{
  "id": "unique-message-id",
  "sender": "agent_id",
  "recipient": "agent_id",
  "type": "task|response|event",
  "payload": {
    // Message-specific data
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Example Messages

### 1. Onboarding: Documentation Query

**Request to Onboarding Agent:**
```json
{
  "id": "msg_001",
  "sender": "supervisor",
  "recipient": "onboarding_agent",
  "type": "task",
  "payload": {
    "task_type": "documentation",
    "customer_id": "customer_123",
    "query": "How do I authenticate API requests?"
  },
  "timestamp": "2024-01-15T10:00:00Z"
}
```

**Response from Onboarding Agent:**
```json
{
  "id": "msg_002",
  "sender": "onboarding_agent",
  "recipient": "supervisor",
  "type": "response",
  "payload": {
    "text": "Found 3 relevant documents for 'How do I authenticate API requests?'",
    "actions": [],
    "attachments": [
      {
        "id": "doc_001",
        "title": "API Authentication Guide",
        "content": "Learn how to authenticate API requests using API keys, OAuth, or JWT tokens...",
        "score": 0.95
      }
    ],
    "metadata": {
      "query": "How do I authenticate API requests?",
      "doc_count": 3
    }
  },
  "timestamp": "2024-01-15T10:00:01Z"
}
```

### 2. Migration Planning

**Request:**
```json
{
  "id": "msg_003",
  "sender": "supervisor",
  "recipient": "onboarding_agent",
  "type": "task",
  "payload": {
    "task_type": "migration_plan",
    "customer_id": "customer_456",
    "source_platform": "AWS",
    "workload_size": "medium",
    "current_infrastructure": {
      "compute": "10 EC2 instances",
      "storage": "500GB RDS",
      "network": "VPC with 3 subnets"
    }
  },
  "timestamp": "2024-01-15T11:00:00Z"
}
```

### 3. Integration Search

**Request:**
```json
{
  "id": "msg_004",
  "sender": "supervisor",
  "recipient": "integration_agent",
  "type": "task",
  "payload": {
    "task_type": "marketplace_search",
    "customer_id": "customer_789",
    "use_case": "payment processing",
    "requirements": ["PCI compliant", "supports subscriptions"]
  },
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### 4. Churn Risk Analysis

**Request:**
```json
{
  "id": "msg_005",
  "sender": "supervisor",
  "recipient": "growth_agent",
  "type": "task",
  "payload": {
    "task_type": "churn_analysis",
    "customer_id": "customer_at_risk"
  },
  "timestamp": "2024-01-15T13:00:00Z"
}
```

**Response:**
```json
{
  "id": "msg_006",
  "sender": "growth_agent",
  "recipient": "supervisor",
  "type": "response",
  "payload": {
    "text": "Churn risk: medium (65%)",
    "actions": [
      {
        "type": "recommend_intervention",
        "intervention": "Schedule check-in call"
      }
    ],
    "attachments": [
      {
        "customer_id": "customer_at_risk",
        "churn_risk_score": 0.65,
        "risk_level": "medium",
        "risk_factors": [
          "Usage declined 40% in last 30 days",
          "3 unresolved support tickets",
          "Billing dispute last month"
        ],
        "recommended_actions": [
          "Schedule check-in call",
          "Offer discount or credits",
          "Prioritize support tickets"
        ]
      }
    ],
    "metadata": {
      "customer_id": "customer_at_risk"
    }
  },
  "timestamp": "2024-01-15T13:00:02Z"
}
```

### 5. Perks Recommendation (HIL Required)

**Request:**
```json
{
  "id": "msg_007",
  "sender": "supervisor",
  "recipient": "growth_agent",
  "type": "task",
  "payload": {
    "task_type": "recommend_perks",
    "customer_id": "customer_high_risk",
    "churn_risk": 0.78
  },
  "timestamp": "2024-01-15T14:00:00Z"
}
```

**Response (requires HIL approval):**
```json
{
  "id": "msg_008",
  "sender": "growth_agent",
  "recipient": "supervisor",
  "type": "response",
  "payload": {
    "text": "Generated 3 perk options",
    "actions": [],
    "attachments": [
      {
        "customer_id": "customer_high_risk",
        "churn_risk": 0.78,
        "options": [
          {
            "type": "discount",
            "description": "25% discount for 3 months",
            "estimated_cost": 375.00,
            "expected_retention_lift": 0.45
          },
          {
            "type": "credits",
            "description": "$500 platform credits",
            "estimated_cost": 500.00,
            "expected_retention_lift": 0.40
          }
        ],
        "recommended": {
          "type": "discount",
          "description": "25% discount for 3 months",
          "estimated_cost": 375.00
        },
        "estimated_cost": 875.00,
        "hil_approval_required": true
      }
    ],
    "metadata": {
      "customer_id": "customer_high_risk",
      "requires_hil_approval": true
    }
  },
  "timestamp": "2024-01-15T14:00:01Z"
}
```

### 6. Platform Status Event

**Event notification:**
```json
{
  "id": "msg_009",
  "sender": "monitoring_system",
  "recipient": "supervisor",
  "type": "event",
  "payload": {
    "event_type": "platform_degradation",
    "severity": "warning",
    "service": "Storage Service",
    "region": "us-west",
    "message": "Increased latency detected",
    "metrics": {
      "avg_latency_ms": 450,
      "normal_latency_ms": 50
    }
  },
  "timestamp": "2024-01-15T15:00:00Z"
}
```

## Message Types

### Task Messages
Sent from supervisor to specialist agents to request action.

### Response Messages
Sent from specialist agents back to sender with results.

### Event Messages
Sent from external systems or monitoring to trigger proactive workflows.

## Agent Response Schema

```json
{
  "text": "Human-readable response",
  "actions": [
    {
      "type": "action_type",
      "param1": "value1"
    }
  ],
  "attachments": [
    {
      "type": "attachment_type",
      "data": {}
    }
  ],
  "metadata": {
    "key": "value"
  }
}
```

## Notes

- All timestamps are in ISO 8601 format (UTC)
- Message IDs should be unique (use UUID)
- Payloads are flexible but should follow agent-specific schemas
- Large attachments should reference external storage, not embed full data
