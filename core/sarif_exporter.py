# core/sarif_exporter.py

from typing import List, Dict
from datetime import datetime


def to_sarif(issues: List[Dict], file_path: str) -> Dict:
    """
    Convert wisdom-ai issues into SARIF 2.1.0 format.
    Deterministic-only. CI-safe.
    """

    sarif_results = []

    for issue in issues:
        loc = issue.get("location") or {}
        line = loc.get("line", 1)
        column = loc.get("column", 1)

        severity = issue.get("severity", "warning")
        level = "error" if severity == "error" else "note"

        sarif_results.append({
            "ruleId": issue["rule_id"],
            "level": level,
            "message": {
                "text": issue["message"]
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_path
                        },
                        "region": {
                            "startLine": line,
                            "startColumn": column
                        }
                    }
                }
            ],
            "properties": {
                "category": issue.get("category"),
                "confidence": issue.get("confidence"),
            }
        })

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "WISDOM AI Sandbox",
                        "informationUri": "https://wisdom-ai-fn24.onrender.com",
                        "version": "wisdom-1.0",
                        "rules": [
                            {
                                "id": issue["rule_id"],
                                "shortDescription": {
                                    "text": issue["message"]
                                },
                                "properties": {
                                    "category": issue.get("category")
                                }
                            }
                            for issue in issues
                        ]
                    }
                },
                "results": sarif_results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "endTimeUtc": datetime.utcnow().isoformat() + "Z"
                    }
                ]
            }
        ]
    }
