"""
Reasoning Validation Module
Validates intermediate reasoning steps and results
"""

from typing import Any, Dict, List, Optional
import json


class ReasoningValidator:
    """Validates reasoning steps and intermediate results"""
    
    @staticmethod
    def validate_tool_result(result: Any, expected_type: type, tool_name: str) -> Dict[str, Any]:
        """
        Validate a tool result
        
        Args:
            result: The result from a tool
            expected_type: Expected type (dict, list, str, etc.)
            tool_name: Name of the tool that produced the result
            
        Returns:
            Dict with validation status and message
        """
        validation = {
            "valid": True,
            "tool": tool_name,
            "message": "Validation passed",
            "issues": []
        }
        
        # Type check
        if not isinstance(result, expected_type):
            validation["valid"] = False
            validation["issues"].append(
                f"Type mismatch: Expected {expected_type.__name__}, got {type(result).__name__}"
            )
        
        # Additional validations based on type
        if isinstance(result, dict):
            # Check for error keys
            if "error" in result:
                validation["valid"] = False
                validation["issues"].append(f"Tool returned error: {result.get('error')}")
            
            # Check if dict is empty (might indicate no results)
            if len(result) == 0:
                validation["issues"].append("Warning: Empty result dictionary")
        
        elif isinstance(result, list):
            # Check if list is empty
            if len(result) == 0:
                validation["issues"].append("Warning: Empty result list")
        
        elif isinstance(result, str):
            # Check for error messages in string
            if "error" in result.lower() or "failed" in result.lower():
                validation["issues"].append("Warning: Result string may contain error message")
        
        if validation["issues"]:
            validation["message"] = "; ".join(validation["issues"])
            if not validation["valid"]:
                validation["message"] = f"Validation failed: {validation['message']}"
        
        return validation
    
    @staticmethod
    def validate_data_consistency(step_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate consistency across multiple reasoning steps
        
        Args:
            step_results: List of step results with 'step', 'tool', 'result' keys
            
        Returns:
            Dict with consistency check results
        """
        consistency = {
            "consistent": True,
            "issues": [],
            "warnings": []
        }
        
        # Check for conflicting results
        lead_ids_seen = set()
        for step in step_results:
            result = step.get("result", {})
            
            # Extract lead IDs if present
            if isinstance(result, list):
                for item in result:
                    if isinstance(item, dict) and "lead_id" in item:
                        lead_id = item["lead_id"]
                        if lead_id in lead_ids_seen:
                            consistency["warnings"].append(
                                f"Lead ID {lead_id} appears in multiple steps"
                            )
                        lead_ids_seen.add(lead_id)
            
            # Check for null/None results
            if result is None:
                consistency["issues"].append(
                    f"Step {step.get('step', 'unknown')} returned None"
                )
                consistency["consistent"] = False
        
        if consistency["issues"]:
            consistency["consistent"] = False
        
        return consistency
    
    @staticmethod
    def validate_calculation(calculation: str, result: float, expected_range: Optional[tuple] = None) -> Dict[str, Any]:
        """
        Validate a calculation result
        
        Args:
            calculation: Description of the calculation
            result: The calculated result
            expected_range: Optional (min, max) tuple for expected range
            
        Returns:
            Dict with validation status
        """
        validation = {
            "valid": True,
            "calculation": calculation,
            "result": result,
            "issues": []
        }
        
        # Check if result is a number
        if not isinstance(result, (int, float)):
            validation["valid"] = False
            validation["issues"].append("Result is not a number")
            return validation
        
        # Check for NaN or Infinity
        import math
        if math.isnan(result) or math.isinf(result):
            validation["valid"] = False
            validation["issues"].append("Result is NaN or Infinity")
        
        # Check expected range
        if expected_range:
            min_val, max_val = expected_range
            if result < min_val or result > max_val:
                validation["valid"] = False
                validation["issues"].append(
                    f"Result {result} outside expected range [{min_val}, {max_val}]"
                )
        
        # Sanity checks
        if result < 0 and "percentage" in calculation.lower():
            validation["valid"] = False
            validation["issues"].append("Percentage cannot be negative")
        
        if result > 100 and "percentage" in calculation.lower():
            validation["valid"] = False
            validation["issues"].append("Percentage cannot exceed 100%")
        
        if validation["issues"]:
            validation["message"] = "; ".join(validation["issues"])
        else:
            validation["message"] = "Calculation validation passed"
        
        return validation
    
    @staticmethod
    def format_validation_report(validations: List[Dict[str, Any]]) -> str:
        """
        Format validation results as a readable report
        
        Args:
            validations: List of validation results
            
        Returns:
            Formatted string report
        """
        report = "## Reasoning Validation Report\n\n"
        
        all_valid = all(v.get("valid", True) for v in validations)
        
        if all_valid:
            report += "✅ **All validations passed**\n\n"
        else:
            report += "⚠️ **Some validations failed**\n\n"
        
        for i, validation in enumerate(validations, 1):
            status = "✅" if validation.get("valid", True) else "❌"
            tool = validation.get("tool", "unknown")
            message = validation.get("message", "No message")
            
            report += f"{status} **Step {i}** ({tool}): {message}\n"
            
            issues = validation.get("issues", [])
            if issues:
                for issue in issues:
                    report += f"   - {issue}\n"
        
        return report

