"""
Prompt Template Engine
======================

Advanced prompt templating system for trading agents with context injection,
tool descriptions, and dynamic prompt building.
"""

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class PromptTemplateEngine:
    """
    Advanced prompt template engine for trading agents.
    
    Features:
    - Template-based prompt generation
    - Context injection
    - Tool description embedding
    - Multi-agent prompt coordination
    - Dynamic prompt adaptation
    """
    
    def __init__(self):
        """Initialize the prompt template engine."""
        self.templates = self._load_default_templates()
        self.context_formatters = self._setup_context_formatters()
    
    def _load_default_templates(self) -> Dict[str, str]:
        """Load default prompt templates."""
        return {
            "analysis_base": """
You are an expert NQ (E-mini NASDAQ-100) futures trading analyst. Your role is to analyze market data and provide actionable trading insights.

## Your Expertise:
- Technical analysis and pattern recognition
- Market microstructure and liquidity analysis  
- Risk assessment and position sizing
- NQ futures contract specifications and behavior

## Current Context:
{context}

## Market Data:
{market_data}

## Available Tools:
{tools}

## Analysis Request:
{request}

Provide a comprehensive analysis including:
1. Market condition assessment
2. Technical indicators summary
3. Pattern recognition results
4. Risk factors and considerations
5. Actionable trading recommendations

Format your response as structured analysis with clear reasoning.
""",

            "execution_base": """
You are a professional NQ futures trade execution specialist. Your role is to execute trades safely and efficiently while managing risk.

## Your Responsibilities:
- Trade execution and order management
- Position monitoring and adjustment
- Risk management implementation
- Compliance with trading rules

## Current Position:
{position_info}

## Market Conditions:
{market_conditions}

## Risk Parameters:
{risk_parameters}

## Execution Request:
{request}

Execute the requested action while ensuring:
1. Proper risk management
2. Optimal execution timing
3. Compliance with position limits
4. Clear documentation of actions

Provide execution details and any required follow-up actions.
""",

            "risk_assessment": """
You are a risk management specialist for NQ futures trading. Your role is to assess and manage trading risks across all positions and strategies.

## Risk Framework:
- Position sizing and exposure limits
- Drawdown monitoring and controls
- Volatility assessment and adjustment
- Portfolio risk aggregation

## Current Portfolio:
{portfolio_status}

## Market Volatility:
{volatility_data}

## Risk Limits:
{risk_limits}

## Assessment Request:
{request}

Provide a comprehensive risk assessment including:
1. Current risk exposure analysis
2. Position sizing recommendations
3. Risk-adjusted performance metrics
4. Early warning indicators
5. Risk mitigation strategies

Ensure all recommendations align with risk management best practices.
""",

            "market_summary": """
Generate a concise market summary for NQ futures:

Current Price: ${current_price:,.2f}
Session Range: ${session_low:,.2f} - ${session_high:,.2f}
Price Change: {price_change:+.2f} ({price_change_pct:+.2f}%)
Volume: {volume:,}
Volatility: {volatility_level}

Key Technical Levels:
- Support: ${support_level:,.2f}
- Resistance: ${resistance_level:,.2f}
- Trend: {trend_direction}

Recent Patterns: {patterns}
Momentum: {momentum_signal}

This summary provides context for {analysis_purpose}.
""",

            "tool_selection": """
Based on the analysis request: "{request}"

Available MCP Tools:
{available_tools}

Recommended tools for this analysis:
{recommended_tools}

Tool usage sequence:
{tool_sequence}

This tool selection optimizes the analysis workflow for accurate results.
"""
        }
    
    def _setup_context_formatters(self) -> Dict[str, callable]:
        """Setup context formatting functions."""
        return {
            "market_data": self._format_market_data,
            "position_info": self._format_position_info,
            "risk_parameters": self._format_risk_parameters,
            "tools": self._format_tools,
            "context": self._format_general_context
        }
    
    def generate_prompt(
        self,
        template_name: str,
        context: Dict[str, Any],
        agent_type: Optional[str] = None,
        tools: Optional[List[str]] = None
    ) -> str:
        """
        Generate a prompt from a template with context injection.
        
        Args:
            template_name: Name of the template to use
            context: Context data to inject
            agent_type: Type of agent (for specialization)
            tools: Available tools to include
            
        Returns:
            Generated prompt string
        """
        try:
            # Get base template
            template = self.templates.get(template_name)
            if not template:
                raise ValueError(f"Template '{template_name}' not found")
            
            # Prepare context data
            formatted_context = self._prepare_context_data(context, tools)
            
            # Add agent-specific modifications
            if agent_type:
                template = self._customize_for_agent(template, agent_type)
            
            # Format template with context
            prompt = template.format(**formatted_context)
            
            # Post-process prompt
            prompt = self._post_process_prompt(prompt)
            
            logger.debug(f"Generated prompt from template '{template_name}' with {len(context)} context items")
            return prompt
            
        except Exception as e:
            logger.error(f"Error generating prompt from template '{template_name}': {e}")
            raise
    
    def _prepare_context_data(self, context: Dict[str, Any], tools: Optional[List[str]] = None) -> Dict[str, str]:
        """Prepare context data for template formatting."""
        formatted_data = {}
        
        # Format each context item using appropriate formatter
        for key, value in context.items():
            formatter = self.context_formatters.get(key, self._format_general_context)
            formatted_data[key] = formatter(value)
        
        # Add tools if provided
        if tools:
            formatted_data['tools'] = self._format_tools(tools)
        else:
            formatted_data['tools'] = "No specific tools required for this analysis."
        
        # Add timestamp
        formatted_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        
        # Ensure all template variables have values
        template_vars = ['context', 'market_data', 'request', 'tools']
        for var in template_vars:
            if var not in formatted_data:
                formatted_data[var] = f"No {var} provided."
        
        return formatted_data
    
    def _customize_for_agent(self, template: str, agent_type: str) -> str:
        """Customize template for specific agent type."""
        customizations = {
            "analysis": {
                "role_emphasis": "Focus on technical analysis and pattern recognition.",
                "output_format": "Provide detailed technical analysis with confidence levels."
            },
            "execution": {
                "role_emphasis": "Prioritize risk management and execution efficiency.",
                "output_format": "Provide clear execution instructions with risk controls."
            },
            "risk": {
                "role_emphasis": "Emphasize risk assessment and mitigation strategies.",
                "output_format": "Quantify risks and provide specific risk management actions."
            }
        }
        
        custom = customizations.get(agent_type, {})
        if custom:
            # Insert customizations into template
            template = f"{custom.get('role_emphasis', '')}\\n\\n{template}\\n\\n{custom.get('output_format', '')}"
        
        return template
    
    def _format_market_data(self, data: Any) -> str:
        """Format market data for prompt inclusion."""
        if isinstance(data, dict):
            if 'current_price' in data:
                return f"""
Current NQ Price: ${data.get('current_price', 0):,.2f}
Session High: ${data.get('session_high', 0):,.2f}
Session Low: ${data.get('session_low', 0):,.2f}
Volume: {data.get('volume', 0):,}
Range: {data.get('range_pct', 0):.2f}%
Position in Range: {data.get('position_in_range', 0):.1f}%
"""
            else:
                return json.dumps(data, indent=2)
        else:
            return str(data)
    
    def _format_position_info(self, data: Any) -> str:
        """Format position information."""
        if isinstance(data, dict):
            return f"""
Position: {data.get('quantity', 0)} contracts
Entry Price: ${data.get('entry_price', 0):,.2f}
Current P&L: ${data.get('unrealized_pnl', 0):,.2f}
Stop Loss: ${data.get('stop_loss', 0):,.2f}
Take Profit: ${data.get('take_profit', 0):,.2f}
"""
        else:
            return str(data)
    
    def _format_risk_parameters(self, data: Any) -> str:
        """Format risk parameters."""
        if isinstance(data, dict):
            return f"""
Max Position Size: {data.get('max_position_pct', 0):.1f}% of account
Daily Loss Limit: {data.get('max_daily_loss_pct', 0):.1f}%
Stop Loss: {data.get('stop_loss_pct', 0):.2f}%
Take Profit: {data.get('take_profit_pct', 0):.2f}%
Max Drawdown: {data.get('max_drawdown_pct', 0):.1f}%
"""
        else:
            return str(data)
    
    def _format_tools(self, tools: Union[List[str], Dict[str, Any]]) -> str:
        """Format available tools."""
        if isinstance(tools, list):
            return "\\n".join([f"- {tool}" for tool in tools])
        elif isinstance(tools, dict):
            formatted = []
            for tool_name, tool_info in tools.items():
                desc = tool_info.get('description', 'No description available')
                formatted.append(f"- {tool_name}: {desc}")
            return "\\n".join(formatted)
        else:
            return str(tools)
    
    def _format_general_context(self, data: Any) -> str:
        """Format general context data."""
        if isinstance(data, (dict, list)):
            return json.dumps(data, indent=2)
        else:
            return str(data)
    
    def _post_process_prompt(self, prompt: str) -> str:
        """Post-process the generated prompt."""
        # Remove excessive whitespace
        lines = prompt.split('\\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()
            if stripped or (cleaned_lines and cleaned_lines[-1]):  # Keep non-empty lines and single empty lines
                cleaned_lines.append(stripped)
        
        # Remove trailing empty lines
        while cleaned_lines and not cleaned_lines[-1]:
            cleaned_lines.pop()
        
        return '\\n'.join(cleaned_lines)
    
    def add_template(self, name: str, template: str) -> None:
        """Add a new prompt template."""
        self.templates[name] = template
        logger.info(f"Added prompt template: {name}")
    
    def get_template_names(self) -> List[str]:
        """Get list of available template names."""
        return list(self.templates.keys())
    
    def validate_template(self, template: str, required_vars: List[str]) -> bool:
        """Validate that template contains required variables."""
        for var in required_vars:
            if f"{{{var}}}" not in template:
                return False
        return True