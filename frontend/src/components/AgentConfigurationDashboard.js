import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Switch,
  FormControlLabel,
  Button,
  Grid,
  Paper,
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Alert,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  Info as InfoIcon,
  Save as SaveIcon,
  FileUpload as UploadIcon,
  FileDownload as DownloadIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  TrendingUp as ChartIcon,
  Assessment as AnalysisIcon,
  Security as RiskIcon
} from '@mui/icons-material';

const AgentConfigurationDashboard = () => {
  // State management
  const [agents, setAgents] = useState([]);
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [configDialogOpen, setConfigDialogOpen] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  const [agentConfig, setAgentConfig] = useState({
    agent_name: '',
    trading_style: 'balanced',
    risk_level: 'moderate',
    max_loss_per_trade_percent: 1.0,
    max_daily_loss_percent: 3.0,
    confidence_required: 0.6,
    use_technical_analysis: true,
    use_ai_analysis: true,
    technical_weight: 0.6,
    ai_weight: 0.4,
    paper_trading_only: true,
    max_trades_per_day: 10,
    max_position_value: 50000
  });
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);

  // Configuration wizard steps
  const wizardSteps = [
    {
      label: 'Basic Information',
      description: 'Set up your agent\'s basic information'
    },
    {
      label: 'Trading Style & Risk',
      description: 'Choose your preferred trading approach and risk level'
    },
    {
      label: 'Analysis Methods',
      description: 'Configure how your agent analyzes the market'
    },
    {
      label: 'Trading Settings',
      description: 'Set trading behavior and safety limits'
    },
    {
      label: 'Review & Create',
      description: 'Review your configuration and create the agent'
    }
  ];

  // Trading style options
  const tradingStyles = [
    { value: 'conservative', label: 'Conservative - Steady, low-risk approach', color: '#4CAF50' },
    { value: 'balanced', label: 'Balanced - Moderate risk and reward', color: '#FF9800' },
    { value: 'aggressive', label: 'Aggressive - Higher risk for higher rewards', color: '#F44336' },
    { value: 'scalper', label: 'Scalper - Quick, frequent trades', color: '#9C27B0' },
    { value: 'swing_trader', label: 'Swing Trader - Hold positions for days/weeks', color: '#2196F3' }
  ];

  // Risk level options
  const riskLevels = [
    { value: 'very_low', label: 'Very Low - Maximum safety', color: '#4CAF50' },
    { value: 'low', label: 'Low - Conservative approach', color: '#8BC34A' },
    { value: 'moderate', label: 'Moderate - Balanced risk', color: '#FF9800' },
    { value: 'high', label: 'High - Aggressive trading', color: '#FF5722' },
    { value: 'very_high', label: 'Very High - Maximum risk', color: '#F44336' }
  ];

  // Load data on component mount
  useEffect(() => {
    loadAgents();
    loadTemplates();
  }, []);

  const loadAgents = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/agents/status');
      const data = await response.json();
      setAgents(Object.entries(data).map(([id, info]) => ({ id, ...info })));
    } catch (error) {
      showAlert('Error loading agents: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/agents/templates');
      const data = await response.json();
      setTemplates(Object.entries(data).map(([name, template]) => ({ name, ...template })));
    } catch (error) {
      showAlert('Error loading templates: ' + error.message, 'error');
    }
  };

  const showAlert = (message, severity = 'info') => {
    const alert = { id: Date.now(), message, severity };
    setAlerts(prev => [...prev, alert]);
    setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.id !== alert.id));
    }, 5000);
  };

  const handleCreateAgent = () => {
    setAgentConfig({
      agent_name: '',
      trading_style: 'balanced',
      risk_level: 'moderate',
      max_loss_per_trade_percent: 1.0,
      max_daily_loss_percent: 3.0,
      confidence_required: 0.6,
      use_technical_analysis: true,
      use_ai_analysis: true,
      technical_weight: 0.6,
      ai_weight: 0.4,
      paper_trading_only: true,
      max_trades_per_day: 10,
      max_position_value: 50000
    });
    setWizardStep(0);
    setConfigDialogOpen(true);
  };

  const handleEditAgent = (agent) => {
    setSelectedAgent(agent);
    // Load agent configuration
    setAgentConfig({
      agent_name: agent.id,
      // ... populate with agent's current config
    });
    setWizardStep(0);
    setConfigDialogOpen(true);
  };

  const handleUseTemplate = (template) => {
    const templateConfig = {
      agent_name: `${template.name} Agent`,
      trading_style: template.default_config?.personality?.analysis_style || 'balanced',
      risk_level: 'moderate', // Would map from template
      // ... map other template values
    };
    setAgentConfig(templateConfig);
    setWizardStep(0);
    setConfigDialogOpen(true);
  };

  const handleWizardNext = () => {
    if (wizardStep < wizardSteps.length - 1) {
      setWizardStep(wizardStep + 1);
    }
  };

  const handleWizardBack = () => {
    if (wizardStep > 0) {
      setWizardStep(wizardStep - 1);
    }
  };

  const handleConfigSubmit = async () => {
    setLoading(true);
    try {
      const endpoint = selectedAgent ? `/api/agents/${selectedAgent.id}/config` : '/api/agents/create';
      const method = selectedAgent ? 'PUT' : 'POST';
      
      const response = await fetch(endpoint, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(agentConfig)
      });

      if (response.ok) {
        showAlert(
          selectedAgent ? 'Agent updated successfully' : 'Agent created successfully',
          'success'
        );
        setConfigDialogOpen(false);
        setSelectedAgent(null);
        await loadAgents();
      } else {
        const error = await response.json();
        showAlert('Error: ' + error.message, 'error');
      }
    } catch (error) {
      showAlert('Error saving agent: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleAgentAction = async (agentId, action) => {
    setLoading(true);
    try {
      const response = await fetch(`/api/agents/${agentId}/${action}`, {
        method: 'POST'
      });

      if (response.ok) {
        showAlert(`Agent ${action} successful`, 'success');
        await loadAgents();
      } else {
        const error = await response.json();
        showAlert('Error: ' + error.message, 'error');
      }
    } catch (error) {
      showAlert(`Error ${action} agent: ` + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  const renderBasicInfoStep = () => (
    <Box sx={{ mt: 2 }}>
      <TextField
        fullWidth
        label="Agent Name"
        value={agentConfig.agent_name}
        onChange={(e) => setAgentConfig({ ...agentConfig, agent_name: e.target.value })}
        placeholder="My Trading Agent"
        margin="normal"
        required
      />
      <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
        Choose a unique name for your trading agent. This will help you identify it in the dashboard.
      </Typography>
    </Box>
  );

  const renderTradingStyleStep = () => (
    <Box sx={{ mt: 2 }}>
      <FormControl fullWidth margin="normal">
        <InputLabel>Trading Style</InputLabel>
        <Select
          value={agentConfig.trading_style}
          onChange={(e) => setAgentConfig({ ...agentConfig, trading_style: e.target.value })}
        >
          {tradingStyles.map((style) => (
            <MenuItem key={style.value} value={style.value}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: style.color,
                    mr: 1
                  }}
                />
                {style.label}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <FormControl fullWidth margin="normal">
        <InputLabel>Risk Level</InputLabel>
        <Select
          value={agentConfig.risk_level}
          onChange={(e) => setAgentConfig({ ...agentConfig, risk_level: e.target.value })}
        >
          {riskLevels.map((level) => (
            <MenuItem key={level.value} value={level.value}>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    backgroundColor: level.color,
                    mr: 1
                  }}
                />
                {level.label}
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>

      <Box sx={{ mt: 3 }}>
        <Typography gutterBottom>Maximum Loss Per Trade: {agentConfig.max_loss_per_trade_percent}%</Typography>
        <Slider
          value={agentConfig.max_loss_per_trade_percent}
          onChange={(e, value) => setAgentConfig({ ...agentConfig, max_loss_per_trade_percent: value })}
          min={0.1}
          max={10}
          step={0.1}
          marks={[
            { value: 0.5, label: '0.5%' },
            { value: 2, label: '2%' },
            { value: 5, label: '5%' },
            { value: 10, label: '10%' }
          ]}
        />
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography gutterBottom>Maximum Daily Loss: {agentConfig.max_daily_loss_percent}%</Typography>
        <Slider
          value={agentConfig.max_daily_loss_percent}
          onChange={(e, value) => setAgentConfig({ ...agentConfig, max_daily_loss_percent: value })}
          min={0.5}
          max={20}
          step={0.5}
          marks={[
            { value: 1, label: '1%' },
            { value: 5, label: '5%' },
            { value: 10, label: '10%' },
            { value: 20, label: '20%' }
          ]}
        />
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography gutterBottom>Minimum Confidence Required: {Math.round(agentConfig.confidence_required * 100)}%</Typography>
        <Slider
          value={agentConfig.confidence_required}
          onChange={(e, value) => setAgentConfig({ ...agentConfig, confidence_required: value })}
          min={0.3}
          max={0.9}
          step={0.1}
          marks={[
            { value: 0.3, label: '30%' },
            { value: 0.5, label: '50%' },
            { value: 0.7, label: '70%' },
            { value: 0.9, label: '90%' }
          ]}
        />
      </Box>
    </Box>
  );

  const renderAnalysisMethodsStep = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>Analysis Methods</Typography>
      
      <FormControlLabel
        control={
          <Switch
            checked={agentConfig.use_technical_analysis}
            onChange={(e) => setAgentConfig({ ...agentConfig, use_technical_analysis: e.target.checked })}
          />
        }
        label="Technical Analysis"
      />
      <Typography variant="body2" color="textSecondary" sx={{ ml: 4, mb: 2 }}>
        Use chart patterns, indicators, and price action analysis
      </Typography>

      <FormControlLabel
        control={
          <Switch
            checked={agentConfig.use_ai_analysis}
            onChange={(e) => setAgentConfig({ ...agentConfig, use_ai_analysis: e.target.checked })}
          />
        }
        label="AI Analysis"
      />
      <Typography variant="body2" color="textSecondary" sx={{ ml: 4, mb: 3 }}>
        Use AI models for market prediction and pattern recognition
      </Typography>

      {agentConfig.use_technical_analysis && (
        <Box sx={{ mt: 3 }}>
          <Typography gutterBottom>Technical Analysis Weight: {Math.round(agentConfig.technical_weight * 100)}%</Typography>
          <Slider
            value={agentConfig.technical_weight}
            onChange={(e, value) => {
              const aiWeight = 1 - value;
              setAgentConfig({
                ...agentConfig,
                technical_weight: value,
                ai_weight: aiWeight
              });
            }}
            min={0}
            max={1}
            step={0.1}
            disabled={!agentConfig.use_ai_analysis}
          />
        </Box>
      )}

      {agentConfig.use_ai_analysis && (
        <Box sx={{ mt: 3 }}>
          <Typography gutterBottom>AI Analysis Weight: {Math.round(agentConfig.ai_weight * 100)}%</Typography>
          <Slider
            value={agentConfig.ai_weight}
            onChange={(e, value) => {
              const technicalWeight = 1 - value;
              setAgentConfig({
                ...agentConfig,
                ai_weight: value,
                technical_weight: technicalWeight
              });
            }}
            min={0}
            max={1}
            step={0.1}
            disabled={!agentConfig.use_technical_analysis}
          />
        </Box>
      )}
    </Box>
  );

  const renderTradingSettingsStep = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>Trading Safety Settings</Typography>
      
      <FormControlLabel
        control={
          <Switch
            checked={agentConfig.paper_trading_only}
            onChange={(e) => setAgentConfig({ ...agentConfig, paper_trading_only: e.target.checked })}
          />
        }
        label="Paper Trading Only (Recommended)"
      />
      <Typography variant="body2" color="textSecondary" sx={{ ml: 4, mb: 2 }}>
        Trade with virtual money only - highly recommended for new agents
      </Typography>

      <TextField
        fullWidth
        type="number"
        label="Maximum Trades Per Day"
        value={agentConfig.max_trades_per_day}
        onChange={(e) => setAgentConfig({ ...agentConfig, max_trades_per_day: parseInt(e.target.value) })}
        margin="normal"
        inputProps={{ min: 1, max: 100 }}
      />

      <TextField
        fullWidth
        type="number"
        label="Maximum Position Value ($)"
        value={agentConfig.max_position_value}
        onChange={(e) => setAgentConfig({ ...agentConfig, max_position_value: parseInt(e.target.value) })}
        margin="normal"
        inputProps={{ min: 1000, max: 1000000, step: 1000 }}
      />
    </Box>
  );

  const renderReviewStep = () => (
    <Box sx={{ mt: 2 }}>
      <Typography variant="h6" gutterBottom>Review Configuration</Typography>
      
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>Basic Information</Typography>
          <Typography>Agent Name: {agentConfig.agent_name}</Typography>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>Trading Style & Risk</Typography>
          <Typography>Style: {tradingStyles.find(s => s.value === agentConfig.trading_style)?.label}</Typography>
          <Typography>Risk Level: {riskLevels.find(r => r.value === agentConfig.risk_level)?.label}</Typography>
          <Typography>Max Loss Per Trade: {agentConfig.max_loss_per_trade_percent}%</Typography>
          <Typography>Max Daily Loss: {agentConfig.max_daily_loss_percent}%</Typography>
          <Typography>Min Confidence: {Math.round(agentConfig.confidence_required * 100)}%</Typography>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>Analysis Methods</Typography>
          <Typography>Technical Analysis: {agentConfig.use_technical_analysis ? 'Enabled' : 'Disabled'}</Typography>
          <Typography>AI Analysis: {agentConfig.use_ai_analysis ? 'Enabled' : 'Disabled'}</Typography>
          {agentConfig.use_technical_analysis && (
            <Typography>Technical Weight: {Math.round(agentConfig.technical_weight * 100)}%</Typography>
          )}
          {agentConfig.use_ai_analysis && (
            <Typography>AI Weight: {Math.round(agentConfig.ai_weight * 100)}%</Typography>
          )}
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="subtitle1" gutterBottom>Trading Settings</Typography>
          <Typography>Paper Trading Only: {agentConfig.paper_trading_only ? 'Yes' : 'No'}</Typography>
          <Typography>Max Trades Per Day: {agentConfig.max_trades_per_day}</Typography>
          <Typography>Max Position Value: ${agentConfig.max_position_value.toLocaleString()}</Typography>
        </CardContent>
      </Card>
    </Box>
  );

  return (
    <Box sx={{ p: 3 }}>
      {/* Alerts */}
      {alerts.map((alert) => (
        <Alert key={alert.id} severity={alert.severity} sx={{ mb: 2 }}>
          {alert.message}
        </Alert>
      ))}

      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Agent Configuration Dashboard
        </Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={handleCreateAgent}
            sx={{ mr: 1 }}
          >
            Create Agent
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadAgents}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Total Agents</Typography>
              <Typography variant="h5">{agents.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Active Agents</Typography>
              <Typography variant="h5">
                {agents.filter(a => a.status === 'active').length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Paper Trading</Typography>
              <Typography variant="h5">
                {agents.filter(a => a.config_summary?.trading_settings?.paper_trading).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>Templates Available</Typography>
              <Typography variant="h5">{templates.length}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Agent Templates */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Agent Templates" />
            <CardContent>
              <List>
                {templates.map((template) => (
                  <ListItem key={template.name}>
                    <ListItemText
                      primary={template.name}
                      secondary={template.description}
                    />
                    <ListItemSecondaryAction>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => handleUseTemplate(template)}
                      >
                        Use
                      </Button>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        {/* Active Agents */}
        <Grid item xs={12} md={8}>
          <Card>
            <CardHeader title="Active Agents" />
            <CardContent>
              {loading && <LinearProgress sx={{ mb: 2 }} />}
              <List>
                {agents.map((agent) => (
                  <ListItem key={agent.id}>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center' }}>
                          {agent.id}
                          <Chip
                            label={agent.status}
                            size="small"
                            color={agent.status === 'active' ? 'success' : 'default'}
                            sx={{ ml: 1 }}
                          />
                          {agent.config_summary?.trading_settings?.paper_trading && (
                            <Chip
                              label="Paper"
                              size="small"
                              color="info"
                              sx={{ ml: 1 }}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2">
                            Type: {agent.agent_type} | 
                            Created: {new Date(agent.created_at).toLocaleDateString()}
                          </Typography>
                          {agent.performance && (
                            <Typography variant="body2" color="textSecondary">
                              Trades: {agent.performance.trades_executed || 0} | 
                              Win Rate: {((agent.performance.win_rate || 0) * 100).toFixed(1)}%
                            </Typography>
                          )}
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box>
                        {agent.status === 'active' ? (
                          <Tooltip title="Pause Agent">
                            <IconButton
                              size="small"
                              onClick={() => handleAgentAction(agent.id, 'pause')}
                            >
                              <PauseIcon />
                            </IconButton>
                          </Tooltip>
                        ) : (
                          <Tooltip title="Start Agent">
                            <IconButton
                              size="small"
                              onClick={() => handleAgentAction(agent.id, 'start')}
                            >
                              <StartIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="Edit Configuration">
                          <IconButton
                            size="small"
                            onClick={() => handleEditAgent(agent)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="View Performance">
                          <IconButton size="small">
                            <ChartIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Configuration Dialog */}
      <Dialog
        open={configDialogOpen}
        onClose={() => setConfigDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          {selectedAgent ? 'Edit Agent Configuration' : 'Create New Trading Agent'}
        </DialogTitle>
        <DialogContent>
          <Stepper activeStep={wizardStep} orientation="vertical">
            {wizardSteps.map((step, index) => (
              <Step key={step.label}>
                <StepLabel>{step.label}</StepLabel>
                <StepContent>
                  <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
                    {step.description}
                  </Typography>
                  {index === 0 && renderBasicInfoStep()}
                  {index === 1 && renderTradingStyleStep()}
                  {index === 2 && renderAnalysisMethodsStep()}
                  {index === 3 && renderTradingSettingsStep()}
                  {index === 4 && renderReviewStep()}
                  <Box sx={{ mt: 2 }}>
                    <Button
                      variant="contained"
                      onClick={index === wizardSteps.length - 1 ? handleConfigSubmit : handleWizardNext}
                      disabled={loading}
                    >
                      {index === wizardSteps.length - 1 ? 'Create Agent' : 'Next'}
                    </Button>
                    {index > 0 && (
                      <Button onClick={handleWizardBack} sx={{ ml: 1 }}>
                        Back
                      </Button>
                    )}
                  </Box>
                </StepContent>
              </Step>
            ))}
          </Stepper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialogOpen(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default AgentConfigurationDashboard;