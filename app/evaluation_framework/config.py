#!/usr/bin/env python3
"""
Configuration file for the LLM-as-a-Judge Evaluation Framework.

This file contains:
- Model configuration
- Call type keywords for validation
- Evaluation rubrics for each call type
- Core and business-specific metrics
"""

import os
from typing import Dict, List, Any

# Model Configuration
MODEL_CONFIG = {
    "model_name": "openai/gpt-oss-120b",  # GPT OSS 120B 128k equivalent
    # "model_name": "llama-3.3-70b-versatile",
    "temperature": 0.0,
    "max_tokens": 15000,
    "api_key": os.getenv("GROQ_API_KEY", ""),
    "reasoning_effort": "medium",
    "service_tier": "auto"
}

# Call Type Keywords for Layer 1 Validation
CALL_TYPE_KEYWORDS = {
    "AE/Sales": [
        "demo", "evaluation", "proposal", "negotiation", "close", "deal", "prospect", 
        "discovery", "qualification", "sales", "pipeline", "forecast", "quota",
        "ae", "account executive", "opportunity", "pipeline", "forecast"
    ],
    "CSM/Post-Sale": [
        "renewal", "upsell", "cross-sell", "health check", "qbr", "quarterly", 
        "adoption", "satisfaction", "roi", "success", "implementation", "onboarding",
        "csm", "customer success", "retention", "expansion"
    ],
    "Internal/Implementation": [
        "implementation", "technical", "configuration", "debugging", "integration",
        "project", "timeline", "milestone", "blocker", "escalation", "technical",
        "engineering", "dev", "development", "code", "bug", "issue"
    ],
    "SDR/Outbound": [
        "outbound", "cold call", "prospecting", "lead", "mql", "sql", "appointment",
        "sdR", "sales development", "outreach", "campaign", "list", "target",
        "cold email", "cold call", "prospect", "lead gen"
    ]
}

# Core Metrics (Applicable to most segments)
CORE_METRICS = [
    "faithfulness",
    "completeness", 
    # "factuality"
]

# Business-Specific Metrics
BUSINESS_METRICS = [
    "business_relevance",
    "action_item_precision",
    "action_item_recall",
    "timeline_accuracy"
]

# Evaluation Rubrics for Each Call Type and Sub-Type
RUBRICS = {
    "AE/Sales": {
        "Discovery/Qualification": {
            "segments": {
                "meeting_context": {
                    "description": "Context for how the meeting was set up and initial rapport.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0, 
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "smart_summary": {
                    "description": "3-5 executive bullet points covering key themes and fit/no-fit indicators.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0, 
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "pain_discovery": {
                    "description": "Specific problems described, their severity, and current workarounds.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "qualification_signals": {
                    "description": "Indicators for Budget, Authority, Need, and Timeline (BANT).",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "competitive_landscape": {
                    "description": "Mention of incumbent tools or alternatives being evaluated along with understanding satisfaction level. This segment requires interpretation. Certain part of the output would be derived from observable transcript signals and direct explicit statements are not expected.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "next_steps": {
                    "description": "Concrete per-person action items with owners and deadlines.",
                    "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                    "weights": {
                        "precision": 1.0,
                        "recall": 1.0,
                        "factuality": 1.0,
                        "timeline_accuracy": 1.0,
                        "owner_attribution": 1.0
                    }
                },
                "closing_remarks": {
                    "description": "Final sentiment, relationship tone, and willingness to continue. This segment requires interpretation. Certain part of the output would be derived from observable transcript signals and direct explicit statements are not expected.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                }
            }
        },
        "Demo/Evaluation": {
            "segments": {
                "meeting_introduction": {
                    "description": "Context regarding prior meeting promises and the specific objectives/scenarios requested for this demo.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "smart_summary": {
                    "description": "3-5 executive bullets highlighting demo peaks, prospect reactions, and overall technical fit/gap status.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "solution_presentation": {
                    "description": "How the product was positioned against pain points, features demonstrated, and specific 'aha' moments.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "technical_fit_and_gaps": {
                    "description": "Requirements met, integration questions, proposed workarounds, and identified feature gaps/requests.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "prospect_reactions": {
                    "description": "Real-time sentiment during the demo—including excitement, skepticism, or confusion—and comparisons to incumbents. This segment requires interpretation. Certain part of the output would be derived from observable transcript signals and direct explicit statements are not expected.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "competitive_landscape": {
                    "description": "Head-to-head comparisons made during the demo and competitive wins/losses cited by the prospect.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "next_steps": {
                    "description": "Commitments moving toward proposal, Proof of Concept (POC), or additional stakeholder technical validation.",
                    "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                    "weights": {
                        "precision": 1.0,
                        "recall": 1.0,
                        "factuality": 1.0,
                        "timeline_accuracy": 1.0,
                        "owner_attribution": 1.0
                    }
                }
            }
        },
        "Proposal/Business Case": {
            "segments": {
                "meeting_context": {
                    "description": "A summary of where the deal stands, a recap of prior stages, and the specific goals for this session.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "smart_summary": {
                    "description": "3-5 executive bullet points covering pricing discussed, stakeholder alignment status, ROI narrative, and blockers to moving forward.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "pricing_discussion": {
                    "description": "Detailed price points, packaging options, volume or multi-year discounts, and the prospect's budget constraints.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "business_case_roi": {
                    "description": "ROI calculations, cost savings, productivity gains, time-to-value projections, and comparisons to the cost of inaction.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "stakeholder_alignment": {
                    "description": "Identification of the economic buyer and champion, positions of blockers, and the status of procurement or legal readiness.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "objections_concerns": {
                    "description": "Specific pushback on price, terms, or timing and how the seller addressed these concerns.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "next_steps": {
                    "description": "Concrete actions to move toward contract delivery, including legal review timelines and final approval dates.",
                    "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                    "weights": {
                        "precision": 1.0,
                        "recall": 1.0,
                        "factuality": 1.0,
                        "timeline_accuracy": 1.0,
                        "owner_attribution": 1.0
                    }
                }
            }
        },
        "Negotiation/Close": {
            "segments": {
                "meeting_context": {
                    "description": "Current deal status, which terms are on the table, and what remains unresolved.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "smart_summary": {
                    "description": "3-5 executive bullet points covering key terms agreed, timeline to close, and remaining blockers.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "commercial_terms": {
                    "description": "Detailed final pricing, discount requests, contract length, SLAs, and payment schedules.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "legal_and_procurement": {
                    "description": "Legal red-lines, security/compliance topics, and status of the procurement workflow.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "concessions": {
                    "description": "Explicit mentions of what the seller gave up (e.g., discounts) versus what the buyer gave up (e.g., longer contract).",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "risk_signals": {
                    "description": "Indicators of stalling, budget freezes, stakeholder changes, or legal impasses. This segment requires interpretation. Certain part of the output would be derived from observable transcript signals and direct explicit statements are not expected.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "path_to_close": {
                    "description": "Specific remaining steps to signature with owners and target dates (e.g., Board approval, PO process).",
                    "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                    "weights": {
                        "precision": 1.0,
                        "recall": 1.0,
                        "factuality": 1.0,
                        "timeline_accuracy": 1.0,
                        "owner_attribution": 1.0
                    }
                }
            }
        }
    },
    "CSM/Post-Sale": {
        "General Health Check": {
            "segments": {
                "relationship_context": {
                    "description": "Account history, tenure, and the specific reason for this call. Extracted account name may have spelling errors so be flexible in matching with Transcript by considering variations in spelling and naming conventions. Do NOT penalize the score if there are spelling errors in the extracted account name as long as it is reasonably clear which account is being referred to.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "smart_summary": {
                    "description": "3-5 executive bullets on overall health, key concerns, and relationship trajectory.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "health_and_adoption": {
                    "description": "Utilization patterns, feature adoption, and expressed satisfaction (NPS/CSAT signals). This segment requires interpretation. Certain part of the output would be derived from observable transcript signals and direct explicit statements are not expected.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "issues_escalations": {
                    "description": "Active support tickets, bugs, and customer frustration levels.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "expansion_signals": {
                    "description": "Interest in new modules, seats, or use cases.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "renewal_risk": {
                    "description": "Discussions on contract timelines, budget cuts, or competitive alternatives.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "action_plan": {
                    "description": "Concrete follow-up actions with owners from both vendor and customer side.",
                    "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                    "weights": {
                        "precision": 1.0,
                        "recall": 1.0,
                        "factuality": 1.0,
                        "timeline_accuracy": 1.0,
                        "owner_attribution": 1.0
                    }
                }
            }
        },
        "QBR": {
            "segments": {
                "performance_review": {
                    "description": "Review of KPIs, success metrics, and ROI delivered in the past quarter.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "success_metrics": {
                    "description": "Forward-looking goals and KPIs agreed upon for the next quarter.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "roadmap_alignment": {
                    "description": "Product roadmap items relevant to this customer and feedback provided.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "renewal_expansion": {
                    "description": "Explicit discussion regarding renewal timelines or expansion modules.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "risk_items": {
                    "description": "Organizational changes, budget freezes, or adoption risks.",
                    "metrics": CORE_METRICS + ["business_relevance"],
                    "weights": {
                        "faithfulness": 1.0,
                        "completeness": 1.0,
                        "factuality": 1.0,
                        "business_relevance": 1.0
                    }
                },
                "joint_action_plan": {
                    "description": "Shared milestones and accountability assignments for both parties.",
                    "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                    "weights": {
                        "precision": 1.0,
                        "recall": 1.0,
                        "factuality": 1.0,
                        "timeline_accuracy": 1.0,
                        "owner_attribution": 1.0
                    }
                }
            }
        }
    },
    "Internal/Implementation": {
        "segments": {
            "meeting_context": {
                "description": "Why the meeting was called, the current project state, and who requested the sync.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "smart_summary": {
                "description": "3-5 executive bullets on what was resolved, what remains open, and a project health signal.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "key_decisions": {
                "description": "Technical or process decisions made, including the rationale and the owner of the decision.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "blockers_risks": {
                "description": "Issues preventing progress (e.g., data mapping errors, resource constraints) and identified risks to the timeline. This segment requires interpretation. Certain part of the output would be derived from observable transcript signals and direct explicit statements are not expected.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "technical_discussion": {
                "description": "Specifics on architecture, schemas, integration logic, debugging steps, and root cause analysis.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "action_items": {
                "description": "Every commitment made. MUST be formatted as [Person]: [Action] - [Timeline].",
                "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                "weights": {
                    "precision": 1.0,
                    "recall": 1.0,
                    "factuality": 1.0,
                    "timeline_accuracy": 1.0,
                    "owner_attribution": 1.0
                }
            },
            "timeline_dependencies": {
                "description": "Upcoming deadlines, milestones, and external dependencies (e.g., waiting for a data upload).",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            }
        }
    },
    "SDR/Outbound": {
        "segments": {
            "call_context": {
                "description": "How the call originated (cold vs. warm), ICP fit, and any prior engagement (email/LinkedIn).",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "smart_summary": {
                "description": "2-3 executive bullets focused on the outcome and prospect's disposition.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "pitch_analysis": {
                "description": "The opening value proposition used and the prospect's initial reaction/engagement level.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "objection_handling": {
                "description": "Specific objections raised (e.g., timing, budget, incumbent) and the SDR's handling quality.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "interest_signals": {
                "description": "Indicators of interest (e.g., feature questions, pricing inquiries) or explicit disinterest.",
                "metrics": CORE_METRICS + ["business_relevance"],
                "weights": {
                    "faithfulness": 1.0,
                    "completeness": 1.0,
                    "factuality": 1.0,
                    "business_relevance": 1.0
                }
            },
            "outcome_metrics": {
                "description": "Final call result, meeting booked (Y/N), materials to send, or referral to an AE.",
                "metrics": ["precision", "recall", "timeline_accuracy", "owner_attribution"],
                "weights": {
                    "precision": 1.0,
                    "recall": 1.0,
                    "factuality": 1.0,
                    "timeline_accuracy": 1.0,
                    "owner_attribution": 1.0
                }
            }
        }
    }
}

# Metric Descriptions for LLM Prompts
METRIC_DESCRIPTIONS = {
    "faithfulness": "Evaluates whether the extracted content is supported by the original transcript",
    "completeness": "Assesses whether all relevant information from the transcript has been captured",
    "factuality": "Verifies the accuracy and truthfulness of the extracted information relative to the transcript",
    "business_relevance": "Evaluates whether the extracted information is relevant to the business context and objectives of the call",
    "precision": "Measures how many of the captured action items are actually present in the transcript",
    "recall": "Measures how many of the actual action items from the transcript were captured",
    "timeline_accuracy": "Evaluates whether timelines and deadlines mentioned in the transcript are accurately captured",
    "owner_attribution": "Assesses the correctness of identifying the responsible party for a given task"
}

# LLM-Based Call Type Validation Prompts
CALL_TYPE_VALIDATION_PROMPTS = {
    "stage1_main_type": """
    You are an expert at classifying sales call types. Analyze the following transcript summary and classify the main call type.

    TRANSCRIPT SUMMARY:
    {transcript_summary}

    Available call types:
    - AE/Sales: Sales calls involving account executives
    - CSM/Post-Sale: Customer success and post-sale calls
    - Internal/Implementation: Internal project and technical calls
    - SDR/Outbound: Sales development and outbound prospecting calls

    Instructions:
    1. Analyze the content, context, and purpose of the call
    2. Identify key indicators that determine the call type
    3. Consider the roles of participants and business objectives

    Provide your response in JSON format:
    {{
        "predicted_call_type": "AE/Sales|CSM/Post-Sale|Internal/Implementation|SDR/Outbound",
        "confidence": number (1-5),
        "reasoning": "Brief explanation for your classification"
    }}

    Be objective and focus on the business context and call purpose.
    """,
    
    "stage2_subtype": """
    You are an expert at classifying AE/Sales call subtypes. Based on the following transcript, classify the specific subtype of this AE/Sales call.

    TRANSCRIPT:
    {transcript}

    Available AE/Sales subtypes:
    - Discovery/Qualification: Initial discovery calls to understand needs and qualify prospects
    - Demo/Evaluation: Product demonstrations and evaluation discussions
    - Proposal/Business Case: Proposal presentations and business case discussions
    - Negotiation/Close: Negotiation and closing discussions

    Instructions:
    1. Analyze the stage of the sales process
    2. Identify the primary purpose and activities
    3. Look for specific indicators of each subtype

    Provide your response in JSON format:
    {{
        "predicted_subtype": "Discovery/Qualification|Demo/Evaluation|Proposal/Business Case|Negotiation/Close",
        "confidence": number (1-5),
        "reasoning": "Brief explanation for your classification"
    }}

    Focus on the sales process stage and primary activities.
    """
}

# Action Item Evaluation Prompt
ACTION_ITEM_EVALUATION_PROMPT = """
You are a segment-level evaluator for structured sales call transcript analysis.

Your task is to:
1. Extract structured counts for precision/recall calculation.
2. Evaluate timeline accuracy.
3. Evaluate owner attribution.

This evaluation is strictly segment-scoped.
Do NOT evaluate beyond what is required by the SEGMENT DESCRIPTION.

------------------------------------------------------------
DEFINITION OF VALID ACTION ITEM
------------------------------------------------------------

For this segment, an "item" refers to a meaningful, actionable next step agreed upon during the meeting.

Valid items should:
- Represent concrete follow-up work or commitments
- Be specific enough to guide post-meeting action
- Be relevant to business progress

Examples of VALID items:
- Send proposal
- Share pricing document
- Schedule technical demo
- Review contract internally
- Provide product documentation

Examples that should NOT be counted as items:
- Routine conversational follow-ups
- Generic check-ins (e.g., "follow up later", "check in", "touch base")
- Vague conversational remarks
- Small talk logistics (e.g., "talk again in an hour")

Only count substantive meeting outcomes that clearly represent actionable next steps.

------------------------------------------------------------
COUNTING RULES
------------------------------------------------------------

1. total_actual_items:
   Number of distinct valid action items explicitly stated in the transcript.

2. total_predicted_items:
   Number of action items listed in the extracted content.

3. captured_items:
   Number of transcript action items that appear in the extracted content
   based on semantic meaning (wording may differ).

4. correct_items:
   Number of predicted items that correspond to a valid action item in the transcript.

Important constraints:

- Matching should be **semantic**, not exact wording.
- Do NOT penalize for incorrect owner attribution.
- Do NOT penalize for incorrect timelines.
- Owner and timeline accuracy are evaluated separately and must NOT affect these counts.
- If a predicted item does not exist in the transcript, it must NOT count as correct.

Do NOT calculate precision or recall. Only return the counts.

------------------------------------------------------------
TIMELINE ACCURACY RULE
------------------------------------------------------------

Evaluate timeline accuracy only for items that include timelines.

Guidelines:
- Do NOT penalize relative timelines (e.g., "next week") if they match the transcript intent.
- Penalize incorrect, swapped, or fabricated timelines.
- If no timelines exist in transcript items for this segment, assign score 5 and explain that no timelines were present.

------------------------------------------------------------
OWNER ATTRIBUTION RULE
------------------------------------------------------------

Evaluate whether responsible parties for action items are correctly identified.

Guidelines:
- Penalize incorrect or swapped ownership.
- If ownership is ambiguous in the transcript, do not penalize.
- If no ownership is specified in transcript items, assign score 5 and explain that ownership was not defined.

------------------------------------------------------------
INPUTS
------------------------------------------------------------

TRANSCRIPT:
{transcript}

SEGMENT NAME:
{segment_name}

SEGMENT DESCRIPTION:
{segment_description}

EXTRACTED CONTENT:
{segment_text}

------------------------------------------------------------
OUTPUT FORMAT (STRICT JSON ONLY)
------------------------------------------------------------

{
  "total_actual_items": number,
  "total_predicted_items": number,
  "captured_items": number,
  "correct_items": number,
  "timeline_accuracy_score": number,
  "timeline_accuracy_reason": "text",
  "owner_attribution_score": number,
  "owner_attribution_reason": "text",
  "analysis": "Brief explanation of how the precision/recall counts were determined. Do NOT discuss timeline or owner evaluation."
}

Do not output any text outside this JSON.
Do not restate instructions.
"""
# ACTION_ITEM_EVALUATION_PROMPT = """
# You are an expert evaluator for sales call transcript analysis.
# Your task is to evaluate the quality of extracted information from a sales call transcript.
# Extracted information is bifurcated into multiple segment. Given the segment name, segment description,
# extracted information for that segment and entire transcript perform the evaluation.

# TRANSCRIPT:
# {transcript}

# SEGMENT NAME: {segment_name}
# SEGMENT DESCRIPTION: {segment_description}
# EXTRACTED CONTENT:
# {segment_text}

# TASK: Extract counts for precision and recall calculation, AND evaluate timeline accuracy AND owner attribution.

# 1. Count total actual items mentioned in the transcript
# 2. Count how many items were captured in the extracted content  
# 3. Count how many captured items are correct (present in transcript)
# 4. Count total predicted items in extracted content
# 5. Evaluate timeline accuracy: Are timelines and deadlines accurately captured? Do NOT penalize for relative timelines (e.g., "Next Week") as long as they are consistent with the transcript, but do penalize for incorrect timelines or missing timelines when they were explicitly mentioned in the transcript?
# 6. Evaluate owner attribution: Are responsible parties correctly identified for each task?

# Scoring Rubric for Timeline Accuracy and Owner Attribution (1-5 scale):
#         Metric: Timeline Accuracy
#         Definition: Degree to which the extracted timelines and deadlines are accurately reflected in the transcript.
#         Score 1: Fails to capture any temporal data even when specific deadlines were agreed upon.
#         Score 2: Assigns the wrong deadline to a task (e.g., "End of Month" instead of "End of Week").
#         Score 3: Identifies that a timeline exists but fails to capture the specific window mentioned.
#         Score 4: Timelines are generally correct but lack specificity (e.g., says "Soon" when the transcript says "By Tuesday").
#         Score 5: All dates (e.g., "Next Friday") are correctly identified and mapped to the correct calendar window.

#         Metric: Owner Attribution
#         Definition: Degree to which the extracted responsible parties for tasks are correctly identified based on the transcript.
#         Score 1: Next steps are listed in passive voice (e.g., "Meeting will be set") with no owner identified.
#         Score 2: Frequent "swapping" of roles (e.g., assigning a "Send Quote" task to the Prospect).
#         Score 3: Significant confusion; at least one major task is assigned to the wrong party.
#         Score 4: One task has an ambiguous owner, but high-stakes tasks are correctly attributed.
#         Score 5: 100 percent of tasks are attributed to the correct speaker (e.g., Seller vs. Buyer).

# Return JSON:
# {{
#     "total_actual_items": number,
#     "captured_items": number,
#     "correct_items": number,
#     "total_predicted_items": number,
#     "timeline_accuracy_score": number (1-5),
#     "timeline_accuracy_reason": "text",
#     "owner_attribution_score": number (1-5),
#     "owner_attribution_reason": "text",
#     "analysis": "brief explanation of counts"
# }}

# Do NOT calculate precision/recall - only extract the counts and evaluate timeline accuracy and owner attribution.
# Do not output any text outside this JSON.
# Do not restate instructions.
# """
