"""
Template engine tool for message generation and customization
"""
from typing import Dict, Any, List, Optional
import re
from datetime import datetime
from .base_tool import BaseAgentTool, ToolResult


class TemplateEngine(BaseAgentTool):
    """Tool for template processing and message generation"""
    
    name: str = "template_engine"
    description: str = (
        "Process message templates with variable substitution, "
        "conditional logic, and dynamic content generation."
    )
    
    def _validate_input(self, **kwargs) -> bool:
        """Validate template engine parameters"""
        operation = kwargs.get('operation')
        if not operation:
            self.logger.error("Operation parameter is required")
            return False
        
        valid_operations = [
            'render_template', 'validate_template', 'extract_variables',
            'create_variations', 'merge_templates', 'optimize_template'
        ]
        
        if operation not in valid_operations:
            self.logger.error(f"Invalid operation: {operation}")
            return False
            
        return True
    
    def _execute(self, **kwargs) -> Dict[str, Any]:
        """Execute template operation"""
        operation = kwargs.get('operation')
        
        try:
            if operation == 'render_template':
                return self._render_template(
                    kwargs.get('template', ''),
                    kwargs.get('variables', {}),
                    kwargs.get('context', {})
                )
            elif operation == 'validate_template':
                return self._validate_template(kwargs.get('template', ''))
            elif operation == 'extract_variables':
                return self._extract_variables(kwargs.get('template', ''))
            elif operation == 'create_variations':
                return self._create_variations(
                    kwargs.get('template', ''),
                    kwargs.get('variation_count', 3)
                )
            elif operation == 'merge_templates':
                return self._merge_templates(
                    kwargs.get('templates', []),
                    kwargs.get('merge_strategy', 'concatenate')
                )
            elif operation == 'optimize_template':
                return self._optimize_template(
                    kwargs.get('template', ''),
                    kwargs.get('optimization_goals', [])
                )
            else:
                raise ValueError(f"Unsupported operation: {operation}")
                
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Template engine operation failed: {str(e)}"
            ).dict()
    
    def _render_template(self, template: str, variables: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Render template with variables and context"""
        if not template:
            return ToolResult(success=False, error="Template is required").dict()
        
        rendered = template
        substitutions_made = []
        errors = []
        
        # Extract all variables from template
        variable_pattern = r'\{([^}]+)\}'
        found_variables = re.findall(variable_pattern, rendered)
        
        # Process each variable
        for var_name in found_variables:
            placeholder = '{' + var_name + '}'
            
            # Handle complex variable expressions
            if '|' in var_name:  # Filters/formatters
                value, substituted = self._process_variable_with_filters(var_name, variables, context)
            elif '?' in var_name:  # Conditional
                value, substituted = self._process_conditional_variable(var_name, variables, context)
            else:  # Simple variable
                value = variables.get(var_name)
                substituted = True if value is not None else False
            
            if substituted and value is not None:
                # Format value based on type
                formatted_value = self._format_variable_value(value, context)
                rendered = rendered.replace(placeholder, str(formatted_value))
                substitutions_made.append({
                    "variable": var_name,
                    "value": formatted_value,
                    "type": type(value).__name__
                })
            elif not substituted:
                # Check for default values
                default_value = self._get_default_value(var_name, context)
                if default_value is not None:
                    rendered = rendered.replace(placeholder, str(default_value))
                    substitutions_made.append({
                        "variable": var_name,
                        "value": default_value,
                        "type": "default"
                    })
                else:
                    errors.append(f"Variable '{var_name}' not found and no default provided")
        
        # Process conditional blocks
        rendered, conditional_results = self._process_conditional_blocks(rendered, variables, context)
        
        # Process loops
        rendered, loop_results = self._process_loops(rendered, variables, context)
        
        # Apply post-processing
        rendered = self._apply_post_processing(rendered, context)
        
        result_data = {
            "original_template": template,
            "rendered_template": rendered,
            "substitutions_made": substitutions_made,
            "conditional_results": conditional_results,
            "loop_results": loop_results,
            "variables_found": found_variables,
            "variables_substituted": len(substitutions_made),
            "errors": errors,
            "success": len(errors) == 0
        }
        
        return ToolResult(
            success=len(errors) == 0,
            data=result_data,
            metadata={"operation": "render_template"}
        ).dict()
    
    def _validate_template(self, template: str) -> Dict[str, Any]:
        """Validate template syntax and structure"""
        validation_issues = []
        warnings = []
        
        # Check for unmatched braces
        open_braces = template.count('{')
        close_braces = template.count('}')
        
        if open_braces != close_braces:
            validation_issues.append(f"Unmatched braces: {open_braces} opening, {close_braces} closing")
        
        # Check for nested braces (not supported in simple implementation)
        nested_pattern = r'\{[^{}]*\{[^{}]*\}[^{}]*\}'
        if re.search(nested_pattern, template):
            warnings.append("Nested braces detected - may not render correctly")
        
        # Extract and validate variables
        variable_pattern = r'\{([^}]+)\}'
        variables = re.findall(variable_pattern, template)
        
        invalid_variables = []
        for var in variables:
            # Check for invalid characters in variable names
            if re.search(r'[^a-zA-Z0-9_|?:.=\s-]', var):
                invalid_variables.append(var)
        
        if invalid_variables:
            validation_issues.append(f"Invalid variable names: {invalid_variables}")
        
        # Check for conditional syntax
        conditional_blocks = re.findall(r'\{%\s*if\s+([^%]+)%\}(.*?)\{%\s*endif\s*%\}', template, re.DOTALL)
        for condition, content in conditional_blocks:
            if not condition.strip():
                validation_issues.append("Empty condition in if block")
        
        # Check template length
        if len(template) > 1000:
            warnings.append("Template is quite long - consider breaking into smaller templates")
        
        # Check for common mistakes
        if '{{' in template or '}}' in template:
            warnings.append("Double braces detected - use single braces for variables")
        
        is_valid = len(validation_issues) == 0
        
        result_data = {
            "is_valid": is_valid,
            "validation_issues": validation_issues,
            "warnings": warnings,
            "variables_found": list(set(variables)),
            "variable_count": len(set(variables)),
            "template_length": len(template),
            "conditional_blocks": len(conditional_blocks)
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "validate_template"}
        ).dict()
    
    def _extract_variables(self, template: str) -> Dict[str, Any]:
        """Extract all variables from template"""
        variable_pattern = r'\{([^}]+)\}'
        raw_variables = re.findall(variable_pattern, template)
        
        processed_variables = []
        
        for var in raw_variables:
            var_info = {
                "name": var,
                "type": "simple",
                "required": True,
                "filters": [],
                "default_value": None
            }
            
            # Check for filters
            if '|' in var:
                parts = var.split('|')
                var_info["name"] = parts[0].strip()
                var_info["filters"] = [f.strip() for f in parts[1:]]
                var_info["type"] = "filtered"
            
            # Check for conditionals
            elif '?' in var:
                var_info["type"] = "conditional"
                var_info["required"] = False
            
            # Check for default values
            if '=' in var_info["name"]:
                name_parts = var_info["name"].split('=')
                var_info["name"] = name_parts[0].strip()
                var_info["default_value"] = name_parts[1].strip()
                var_info["required"] = False
            
            processed_variables.append(var_info)
        
        # Remove duplicates
        unique_variables = []
        seen_names = set()
        
        for var in processed_variables:
            if var["name"] not in seen_names:
                unique_variables.append(var)
                seen_names.add(var["name"])
        
        # Categorize variables
        required_vars = [v for v in unique_variables if v["required"]]
        optional_vars = [v for v in unique_variables if not v["required"]]
        filtered_vars = [v for v in unique_variables if v["type"] == "filtered"]
        conditional_vars = [v for v in unique_variables if v["type"] == "conditional"]
        
        result_data = {
            "all_variables": unique_variables,
            "required_variables": required_vars,
            "optional_variables": optional_vars,
            "filtered_variables": filtered_vars,
            "conditional_variables": conditional_vars,
            "total_unique_variables": len(unique_variables),
            "variable_names": [v["name"] for v in unique_variables]
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "extract_variables"}
        ).dict()
    
    def _create_variations(self, template: str, variation_count: int = 3) -> Dict[str, Any]:
        """Create variations of a template"""
        variations = []
        
        for i in range(variation_count):
            variation = {
                "variation_id": f"var_{i+1}",
                "template": template,
                "modifications": []
            }
            
            # Apply different modification strategies
            if i == 0:
                # Formal variation
                variation["template"], mods = self._apply_formal_tone(template)
                variation["tone"] = "formal"
                variation["modifications"] = mods
            elif i == 1:
                # Casual variation
                variation["template"], mods = self._apply_casual_tone(template)
                variation["tone"] = "casual"
                variation["modifications"] = mods
            else:
                # Emotional variation
                variation["template"], mods = self._apply_emotional_tone(template)
                variation["tone"] = "emotional"
                variation["modifications"] = mods
            
            # Add metadata
            variation["word_count"] = len(variation["template"].split())
            variation["character_count"] = len(variation["template"])
            
            variations.append(variation)
        
        result_data = {
            "original_template": template,
            "variations": variations,
            "variation_count": len(variations)
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "create_variations"}
        ).dict()
    
    def _merge_templates(self, templates: List[str], merge_strategy: str = 'concatenate') -> Dict[str, Any]:
        """Merge multiple templates"""
        if not templates:
            return ToolResult(success=False, error="No templates provided").dict()
        
        if merge_strategy == 'concatenate':
            merged = '\n\n'.join(templates)
            merge_info = "Templates concatenated with double newlines"
            
        elif merge_strategy == 'interleave':
            # Interleave sentences from each template
            all_sentences = []
            for template in templates:
                sentences = re.split(r'[.!?]+', template)
                sentences = [s.strip() for s in sentences if s.strip()]
                all_sentences.extend(sentences)
            merged = '. '.join(all_sentences) + '.'
            merge_info = "Sentences from templates interleaved"
            
        elif merge_strategy == 'best_parts':
            # Take the longest sentence from each template
            best_parts = []
            for template in templates:
                sentences = re.split(r'[.!?]+', template)
                sentences = [s.strip() for s in sentences if s.strip()]
                if sentences:
                    longest = max(sentences, key=len)
                    best_parts.append(longest)
            merged = '. '.join(best_parts) + '.'
            merge_info = "Best parts from each template combined"
            
        else:  # Default to concatenate
            merged = ' '.join(templates)
            merge_info = "Templates joined with spaces"
        
        # Extract variables from merged template
        extraction_result = self._extract_variables(merged)
        variables = extraction_result['data']['all_variables']
        
        result_data = {
            "original_templates": templates,
            "merged_template": merged,
            "merge_strategy": merge_strategy,
            "merge_info": merge_info,
            "original_count": len(templates),
            "merged_length": len(merged),
            "variables_in_merged": variables
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "merge_templates"}
        ).dict()
    
    def _optimize_template(self, template: str, optimization_goals: List[str]) -> Dict[str, Any]:
        """Optimize template based on goals"""
        optimized = template
        optimizations_applied = []
        
        for goal in optimization_goals:
            if goal == 'reduce_length':
                optimized, changes = self._reduce_template_length(optimized)
                optimizations_applied.extend(changes)
                
            elif goal == 'improve_clarity':
                optimized, changes = self._improve_template_clarity(optimized)
                optimizations_applied.extend(changes)
                
            elif goal == 'increase_personalization':
                optimized, changes = self._increase_personalization(optimized)
                optimizations_applied.extend(changes)
                
            elif goal == 'mobile_friendly':
                optimized, changes = self._make_mobile_friendly(optimized)
                optimizations_applied.extend(changes)
        
        # Calculate improvement metrics
        original_length = len(template)
        optimized_length = len(optimized)
        length_change = ((optimized_length - original_length) / original_length) * 100
        
        result_data = {
            "original_template": template,
            "optimized_template": optimized,
            "optimization_goals": optimization_goals,
            "optimizations_applied": optimizations_applied,
            "metrics": {
                "original_length": original_length,
                "optimized_length": optimized_length,
                "length_change_percent": round(length_change, 2),
                "optimizations_count": len(optimizations_applied)
            }
        }
        
        return ToolResult(
            success=True,
            data=result_data,
            metadata={"operation": "optimize_template"}
        ).dict()
    
    # Helper methods
    def _process_variable_with_filters(self, var_expression: str, variables: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Process variable with filters like {name|upper|trim}"""
        parts = var_expression.split('|')
        var_name = parts[0].strip()
        filters = [f.strip() for f in parts[1:]]
        
        value = variables.get(var_name)
        if value is None:
            return None, False
        
        # Apply filters
        for filter_name in filters:
            value = self._apply_filter(value, filter_name, context)
        
        return value, True
    
    def _process_conditional_variable(self, var_expression: str, variables: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Process conditional variable like {name?'Hello {name}':'Hello there'}"""
        if '?' not in var_expression:
            return None, False
        
        parts = var_expression.split('?', 1)
        condition = parts[0].strip()
        
        if ':' in parts[1]:
            true_part, false_part = parts[1].split(':', 1)
            true_value = true_part.strip().strip("'\"")
            false_value = false_part.strip().strip("'\"")
        else:
            true_value = parts[1].strip().strip("'\"")
            false_value = ""
        
        # Evaluate condition
        condition_result = self._evaluate_condition(condition, variables, context)
        
        return true_value if condition_result else false_value, True
    
    def _apply_filter(self, value: Any, filter_name: str, context: Dict[str, Any]) -> Any:
        """Apply a filter to a value"""
        if filter_name == 'upper':
            return str(value).upper() if value else value
        elif filter_name == 'lower':
            return str(value).lower() if value else value
        elif filter_name == 'title':
            return str(value).title() if value else value
        elif filter_name == 'trim':
            return str(value).strip() if value else value
        elif filter_name == 'length':
            return len(str(value)) if value else 0
        elif filter_name == 'default':
            return value if value else context.get('default_value', '')
        else:
            return value
    
    def _evaluate_condition(self, condition: str, variables: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a simple condition"""
        # Simple condition evaluation
        condition = condition.strip()
        
        if condition in variables:
            value = variables[condition]
            return bool(value) and value != "" and value is not None
        
        return False
    
    def _format_variable_value(self, value: Any, context: Dict[str, Any]) -> str:
        """Format variable value based on type and context"""
        if isinstance(value, datetime):
            return value.strftime(context.get('date_format', '%Y-%m-%d'))
        elif isinstance(value, (int, float)):
            if 'number_format' in context:
                return context['number_format'].format(value)
            return str(value)
        elif isinstance(value, list):
            return ', '.join(str(item) for item in value)
        else:
            return str(value)
    
    def _get_default_value(self, var_name: str, context: Dict[str, Any]) -> Optional[str]:
        """Get default value for a variable"""
        defaults = context.get('defaults', {})
        
        # Common defaults
        common_defaults = {
            'name': 'عزيزنا العميل',
            'customer_name': 'valued customer',
            'restaurant_name': 'مطعمنا',
            'date': datetime.now().strftime('%Y-%m-%d')
        }
        
        return defaults.get(var_name) or common_defaults.get(var_name)
    
    def _process_conditional_blocks(self, template: str, variables: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Process conditional blocks like {% if condition %}content{% endif %}"""
        conditional_pattern = r'\{%\s*if\s+([^%]+)%\}(.*?)\{%\s*endif\s*%\}'
        matches = re.findall(conditional_pattern, template, re.DOTALL)
        
        results = []
        processed_template = template
        
        for condition, content in matches:
            condition_result = self._evaluate_condition(condition.strip(), variables, context)
            
            # Replace the conditional block
            full_block = f"{{% if {condition} %}}{content}{{% endif %}}"
            
            if condition_result:
                processed_template = processed_template.replace(full_block, content)
            else:
                processed_template = processed_template.replace(full_block, "")
            
            results.append({
                "condition": condition.strip(),
                "result": condition_result,
                "content_included": condition_result
            })
        
        return processed_template, results
    
    def _process_loops(self, template: str, variables: Dict[str, Any], context: Dict[str, Any]) -> tuple:
        """Process loop blocks like {% for item in items %}content{% endfor %}"""
        loop_pattern = r'\{%\s*for\s+(\w+)\s+in\s+(\w+)\s*%\}(.*?)\{%\s*endfor\s*%\}'
        matches = re.findall(loop_pattern, template, re.DOTALL)
        
        results = []
        processed_template = template
        
        for loop_var, collection_name, content in matches:
            collection = variables.get(collection_name, [])
            
            if isinstance(collection, list):
                loop_content = []
                for item in collection:
                    item_content = content.replace(f'{{{loop_var}}}', str(item))
                    loop_content.append(item_content)
                
                full_block = f"{{% for {loop_var} in {collection_name} %}}{content}{{% endfor %}}"
                processed_template = processed_template.replace(full_block, ''.join(loop_content))
                
                results.append({
                    "loop_variable": loop_var,
                    "collection": collection_name,
                    "items_processed": len(collection),
                    "success": True
                })
            else:
                results.append({
                    "loop_variable": loop_var,
                    "collection": collection_name,
                    "items_processed": 0,
                    "success": False,
                    "error": f"Collection '{collection_name}' is not a list"
                })
        
        return processed_template, results
    
    def _apply_post_processing(self, template: str, context: Dict[str, Any]) -> str:
        """Apply final post-processing to template"""
        processed = template
        
        # Remove empty lines
        if context.get('remove_empty_lines', True):
            processed = re.sub(r'\n\s*\n', '\n', processed)
        
        # Trim whitespace
        if context.get('trim_whitespace', True):
            processed = processed.strip()
        
        # Fix multiple spaces
        if context.get('fix_spacing', True):
            processed = re.sub(r' +', ' ', processed)
        
        return processed
    
    def _apply_formal_tone(self, template: str) -> tuple:
        """Apply formal tone modifications"""
        modified = template
        modifications = []
        
        # Replace casual words with formal equivalents
        casual_to_formal = {
            'hey': 'greetings',
            'thanks': 'thank you',
            'awesome': 'excellent',
            'great': 'outstanding'
        }
        
        for casual, formal in casual_to_formal.items():
            if casual in modified.lower():
                modified = re.sub(casual, formal, modified, flags=re.IGNORECASE)
                modifications.append(f"Replaced '{casual}' with '{formal}'")
        
        return modified, modifications
    
    def _apply_casual_tone(self, template: str) -> tuple:
        """Apply casual tone modifications"""
        modified = template
        modifications = []
        
        # Replace formal words with casual equivalents
        formal_to_casual = {
            'greetings': 'hey',
            'thank you': 'thanks',
            'excellent': 'great',
            'outstanding': 'awesome'
        }
        
        for formal, casual in formal_to_casual.items():
            if formal in modified.lower():
                modified = re.sub(formal, casual, modified, flags=re.IGNORECASE)
                modifications.append(f"Replaced '{formal}' with '{casual}'")
        
        return modified, modifications
    
    def _apply_emotional_tone(self, template: str) -> tuple:
        """Apply emotional tone modifications"""
        modified = template
        modifications = []
        
        # Add emotional words
        if not any(word in modified.lower() for word in ['!', 'amazing', 'wonderful', 'fantastic']):
            # Add excitement
            modified = modified.replace('.', '!')
            modifications.append("Added exclamation marks for emphasis")
        
        return modified, modifications
    
    def _reduce_template_length(self, template: str) -> tuple:
        """Reduce template length"""
        modified = template
        changes = []
        
        # Remove redundant words
        redundant_patterns = [
            (r'\bvery\s+', ''),
            (r'\breally\s+', ''),
            (r'\bquite\s+', ''),
        ]
        
        for pattern, replacement in redundant_patterns:
            if re.search(pattern, modified):
                modified = re.sub(pattern, replacement, modified)
                changes.append(f"Removed redundant words matching '{pattern}'")
        
        return modified, changes
    
    def _improve_template_clarity(self, template: str) -> tuple:
        """Improve template clarity"""
        modified = template
        changes = []
        
        # Break long sentences
        if len(template) > 100:
            # Simple sentence breaking
            modified = template.replace(',', '.')
            changes.append("Broke long sentences for clarity")
        
        return modified, changes
    
    def _increase_personalization(self, template: str) -> tuple:
        """Increase template personalization"""
        modified = template
        changes = []
        
        # Add more personalization variables
        if '{name}' not in modified and 'name' not in modified:
            modified = '{name}, ' + modified
            changes.append("Added name personalization")
        
        return modified, changes
    
    def _make_mobile_friendly(self, template: str) -> tuple:
        """Make template mobile-friendly"""
        modified = template
        changes = []
        
        # Shorten for mobile
        if len(template) > 160:
            sentences = re.split(r'[.!?]+', template)
            if len(sentences) > 1:
                modified = sentences[0] + '.'
                changes.append("Shortened for mobile display")
        
        return modified, changes