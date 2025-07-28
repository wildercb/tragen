import React, { useState, useEffect, useRef } from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  Typography,
  Button,
  Grid,
  Box,
  Paper,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Slider,
  Rating,
  Chip,
  List,
  ListItem,
  ListItemText,
  Alert,
  Tabs,
  Tab,
  IconButton,
  Tooltip,
  Divider
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  School as TrainIcon,
  ChatBubble as ChatIcon,
  Timeline as ChartIcon,
  Feedback as FeedbackIcon,
  TrendingUp as SignalIcon,
  Note as AnnotationIcon,
  QuestionAnswer as QuestionIcon,
  Send as SendIcon,
  Clear as ClearIcon,
  Fullscreen as FullscreenIcon
} from '@mui/icons-material';

const LiveTrainingInterface = ({ agentId }) => {
  // State management
  const [trainingSession, setTrainingSession] = useState(null);
  const [sessionActive, setSessionActive] = useState(false);
  const [selectedSymbol, setSelectedSymbol] = useState('NQ=F');
  const [selectedTimeframe, setSelectedTimeframe] = useState('15m');
  const [trainingMode, setTrainingMode] = useState('simulation');
  const [activeTab, setActiveTab] = useState(0);
  
  // Chart and annotation state
  const [chartAnnotations, setChartAnnotations] = useState([]);
  const [selectedAnnotationType, setSelectedAnnotationType] = useState('note');
  const [annotationText, setAnnotationText] = useState('');
  
  // Feedback state
  const [feedbackDialog, setFeedbackDialog] = useState(false);
  const [feedbackRating, setFeedbackRating] = useState(3);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackCategory, setFeedbackCategory] = useState('general');
  
  // Chat state
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [agentTyping, setAgentTyping] = useState(false);
  
  // Recent events
  const [recentEvents, setRecentEvents] = useState([]);
  const [agentAnalysis, setAgentAnalysis] = useState(null);
  
  // WebSocket connection
  const wsRef = useRef(null);
  const chartRef = useRef(null);

  // Training modes
  const trainingModes = [
    { value: 'observation', label: 'Observation - Agent watches your actions' },
    { value: 'simulation', label: 'Simulation - Agent makes decisions, you provide feedback' },
    { value: 'collaborative', label: 'Collaborative - Work together with the agent' },
    { value: 'evaluation', label: 'Evaluation - Test agent performance' }
  ];

  // Annotation types
  const annotationTypes = [
    { value: 'note', label: 'Note', color: '#2196F3' },
    { value: 'support_level', label: 'Support Level', color: '#4CAF50' },
    { value: 'resistance_level', label: 'Resistance Level', color: '#F44336' },
    { value: 'trend_line', label: 'Trend Line', color: '#FF9800' },
    { value: 'entry_point', label: 'Entry Point', color: '#9C27B0' },
    { value: 'exit_point', label: 'Exit Point', color: '#E91E63' },
    { value: 'pattern_highlight', label: 'Pattern', color: '#00BCD4' }
  ];

  // Feedback categories
  const feedbackCategories = [
    { value: 'decision_making', label: 'Decision Making' },
    { value: 'timing', label: 'Timing' },
    { value: 'risk_management', label: 'Risk Management' },
    { value: 'analysis_quality', label: 'Analysis Quality' },
    { value: 'reasoning', label: 'Reasoning' },
    { value: 'general', label: 'General' }
  ];

  useEffect(() => {
    if (sessionActive && trainingSession) {
      initializeWebSocket();
    }
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [sessionActive, trainingSession]);

  const initializeWebSocket = () => {
    const wsUrl = `ws://localhost:8000/ws/training/${trainingSession.session_id}`;
    wsRef.current = new WebSocket(wsUrl);

    wsRef.current.onopen = () => {
      console.log('Training WebSocket connected');
    };

    wsRef.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWebSocketMessage(data);
    };

    wsRef.current.onclose = () => {
      console.log('Training WebSocket disconnected');
    };
  };

  const handleWebSocketMessage = (data) => {
    switch (data.type) {
      case 'training_event':
        setRecentEvents(prev => [data.event, ...prev.slice(0, 9)]);
        break;
      case 'agent_analysis':
        setAgentAnalysis(data.analysis);
        break;
      case 'agent_message':
        setChatMessages(prev => [...prev, {
          type: 'agent',
          message: data.message,
          timestamp: new Date()
        }]);
        setAgentTyping(false);
        break;
      default:
        console.log('Unknown WebSocket message:', data);
    }
  };

  const startTrainingSession = async () => {
    try {
      const response = await fetch('/api/training/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agentId,
          mode: trainingMode,
          symbol: selectedSymbol,
          timeframe: selectedTimeframe
        })
      });

      if (response.ok) {
        const session = await response.json();
        setTrainingSession(session);
        setSessionActive(true);
      }
    } catch (error) {
      console.error('Failed to start training session:', error);
    }
  };

  const endTrainingSession = async () => {
    if (!trainingSession) return;

    try {
      const response = await fetch(`/api/training/end/${trainingSession.session_id}`, {
        method: 'POST'
      });

      if (response.ok) {
        const summary = await response.json();
        console.log('Training session summary:', summary);
        setSessionActive(false);
        setTrainingSession(null);
        
        if (wsRef.current) {
          wsRef.current.close();
        }
      }
    } catch (error) {
      console.error('Failed to end training session:', error);
    }
  };

  const handleChartClick = async (event) => {
    if (!sessionActive || !trainingSession) return;

    const rect = chartRef.current.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // Convert screen coordinates to chart coordinates (simplified)
    const chartTime = new Date(); // Would calculate actual chart time
    const priceLevel = 15000 + (400 - y) * 10; // Simplified price calculation

    const annotationData = {
      type: selectedAnnotationType,
      x: x,
      y: y,
      price_level: priceLevel,
      chart_time: chartTime.toISOString(),
      text: annotationText,
      color: annotationTypes.find(t => t.value === selectedAnnotationType)?.color || '#2196F3'
    };

    try {
      const response = await fetch(`/api/training/annotate/${trainingSession.session_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(annotationData)
      });

      if (response.ok) {
        const annotation = await response.json();
        setChartAnnotations(prev => [...prev, annotation]);
        setAnnotationText('');
      }
    } catch (error) {
      console.error('Failed to add annotation:', error);
    }
  };

  const submitFeedback = async () => {
    if (!sessionActive || !trainingSession) return;

    const feedbackData = {
      type: feedbackRating >= 4 ? 'positive' : feedbackRating <= 2 ? 'negative' : 'rating',
      category: feedbackCategory,
      rating: feedbackRating,
      comment: feedbackComment
    };

    try {
      const response = await fetch(`/api/training/feedback/${trainingSession.session_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(feedbackData)
      });

      if (response.ok) {
        setFeedbackDialog(false);
        setFeedbackComment('');
        setFeedbackRating(3);
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || !sessionActive || !trainingSession) return;

    const userMessage = {
      type: 'user',
      message: chatInput,
      timestamp: new Date()
    };

    setChatMessages(prev => [...prev, userMessage]);
    setAgentTyping(true);

    try {
      const response = await fetch(`/api/training/question/${trainingSession.session_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: chatInput,
          context: { current_price: 15000 } // Would include actual market context
        })
      });

      if (response.ok) {
        const result = await response.json();
        setChatMessages(prev => [...prev, {
          type: 'agent',
          message: result.response,
          timestamp: new Date()
        }]);
      }
    } catch (error) {
      console.error('Failed to send question:', error);
    } finally {
      setChatInput('');
      setAgentTyping(false);
    }
  };

  const requestAgentAnalysis = async () => {
    if (!sessionActive || !trainingSession) return;

    try {
      const response = await fetch(`/api/training/analysis/${trainingSession.session_id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symbol: selectedSymbol,
          timeframe: selectedTimeframe
        })
      });

      if (response.ok) {
        const analysis = await response.json();
        setAgentAnalysis(analysis);
      }
    } catch (error) {
      console.error('Failed to get agent analysis:', error);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">Live Training Interface</Typography>
        <Box>
          {!sessionActive ? (
            <Button
              variant="contained"
              startIcon={<StartIcon />}
              onClick={startTrainingSession}
            >
              Start Training
            </Button>
          ) : (
            <Button
              variant="outlined"
              startIcon={<StopIcon />}
              onClick={endTrainingSession}
            >
              End Session
            </Button>
          )}
        </Box>
      </Box>

      {/* Session Setup */}
      {!sessionActive && (
        <Card sx={{ mb: 3 }}>
          <CardHeader title="Training Session Setup" />
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Training Mode</InputLabel>
                  <Select
                    value={trainingMode}
                    onChange={(e) => setTrainingMode(e.target.value)}
                  >
                    {trainingModes.map((mode) => (
                      <MenuItem key={mode.value} value={mode.value}>
                        {mode.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <TextField
                  fullWidth
                  label="Symbol"
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                />
              </Grid>
              <Grid item xs={12} md={3}>
                <FormControl fullWidth>
                  <InputLabel>Timeframe</InputLabel>
                  <Select
                    value={selectedTimeframe}
                    onChange={(e) => setSelectedTimeframe(e.target.value)}
                  >
                    <MenuItem value="1m">1 Minute</MenuItem>
                    <MenuItem value="5m">5 Minutes</MenuItem>
                    <MenuItem value="15m">15 Minutes</MenuItem>
                    <MenuItem value="1h">1 Hour</MenuItem>
                    <MenuItem value="4h">4 Hours</MenuItem>
                    <MenuItem value="1d">1 Day</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={3}>
                <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                  Agent: {agentId}
                </Typography>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Active Session Interface */}
      {sessionActive && (
        <>
          {/* Session Status */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={3}>
                  <Typography variant="h6" color="primary">Session Active</Typography>
                  <Typography variant="body2">
                    Mode: {trainingModes.find(m => m.value === trainingMode)?.label.split(' -')[0]}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="textSecondary">Symbol</Typography>
                  <Typography variant="h6">{selectedSymbol}</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="textSecondary">Timeframe</Typography>
                  <Typography variant="h6">{selectedTimeframe}</Typography>
                </Grid>
                <Grid item xs={12} md={3}>
                  <Typography variant="body2" color="textSecondary">Events</Typography>
                  <Typography variant="h6">{recentEvents.length}</Typography>
                </Grid>
              </Grid>
            </CardContent>
          </Card>

          {/* Main Interface */}
          <Grid container spacing={3}>
            {/* Chart and Tools */}
            <Grid item xs={12} md={8}>
              <Card>
                <CardHeader 
                  title="Interactive Chart"
                  action={
                    <Box>
                      <Button
                        size="small"
                        startIcon={<SignalIcon />}
                        onClick={requestAgentAnalysis}
                        sx={{ mr: 1 }}
                      >
                        Get Analysis
                      </Button>
                      <IconButton>
                        <FullscreenIcon />
                      </IconButton>
                    </Box>
                  }
                />
                <CardContent>
                  {/* Chart Annotation Tools */}
                  <Box sx={{ mb: 2, display: 'flex', alignItems: 'center', gap: 2 }}>
                    <FormControl size="small" sx={{ minWidth: 150 }}>
                      <InputLabel>Annotation Type</InputLabel>
                      <Select
                        value={selectedAnnotationType}
                        onChange={(e) => setSelectedAnnotationType(e.target.value)}
                      >
                        {annotationTypes.map((type) => (
                          <MenuItem key={type.value} value={type.value}>
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Box
                                sx={{
                                  width: 12,
                                  height: 12,
                                  borderRadius: '50%',
                                  backgroundColor: type.color,
                                  mr: 1
                                }}
                              />
                              {type.label}
                            </Box>
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                    <TextField
                      size="small"
                      placeholder="Annotation text..."
                      value={annotationText}
                      onChange={(e) => setAnnotationText(e.target.value)}
                      sx={{ flexGrow: 1 }}
                    />
                  </Box>

                  {/* Mock Chart Area */}
                  <Paper
                    ref={chartRef}
                    sx={{
                      height: 400,
                      backgroundColor: '#1a1a1a',
                      position: 'relative',
                      cursor: 'crosshair',
                      border: '1px solid #333'
                    }}
                    onClick={handleChartClick}
                  >
                    <Box
                      sx={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        transform: 'translate(-50%, -50%)',
                        color: '#666',
                        textAlign: 'center'
                      }}
                    >
                      <ChartIcon sx={{ fontSize: 60, mb: 1 }} />
                      <Typography variant="h6">Interactive Trading Chart</Typography>
                      <Typography variant="body2">
                        Click to add annotations • {selectedSymbol} • {selectedTimeframe}
                      </Typography>
                    </Box>

                    {/* Render Annotations */}
                    {chartAnnotations.map((annotation, index) => (
                      <Box
                        key={index}
                        sx={{
                          position: 'absolute',
                          left: annotation.x,
                          top: annotation.y,
                          width: 10,
                          height: 10,
                          borderRadius: '50%',
                          backgroundColor: annotation.color,
                          cursor: 'pointer'
                        }}
                      />
                    ))}
                  </Paper>

                  {/* Agent Analysis Display */}
                  {agentAnalysis && (
                    <Alert severity="info" sx={{ mt: 2 }}>
                      <Typography variant="subtitle2">Agent Analysis</Typography>
                      <Typography variant="body2">
                        Action: {agentAnalysis.analysis?.action} | 
                        Confidence: {Math.round((agentAnalysis.analysis?.confidence || 0) * 100)}%
                      </Typography>
                      <Typography variant="body2">
                        {agentAnalysis.analysis?.reasoning}
                      </Typography>
                    </Alert>
                  )}
                </CardContent>
              </Card>
            </Grid>

            {/* Side Panel */}
            <Grid item xs={12} md={4}>
              <Paper sx={{ height: 600 }}>
                <Tabs
                  value={activeTab}
                  onChange={(e, newValue) => setActiveTab(newValue)}
                  variant="fullWidth"
                >
                  <Tab label="Chat" icon={<ChatIcon />} />
                  <Tab label="Events" icon={<TrainIcon />} />
                  <Tab label="Feedback" icon={<FeedbackIcon />} />
                </Tabs>

                {/* Chat Tab */}
                {activeTab === 0 && (
                  <Box sx={{ p: 2, height: 'calc(100% - 48px)', display: 'flex', flexDirection: 'column' }}>
                    <Box sx={{ flexGrow: 1, overflowY: 'auto', mb: 2 }}>
                      {chatMessages.map((msg, index) => (
                        <Box
                          key={index}
                          sx={{
                            mb: 1,
                            p: 1,
                            borderRadius: 1,
                            backgroundColor: msg.type === 'user' ? '#e3f2fd' : '#f5f5f5',
                            marginLeft: msg.type === 'user' ? 2 : 0,
                            marginRight: msg.type === 'agent' ? 2 : 0
                          }}
                        >
                          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
                            {msg.type === 'user' ? 'You' : 'Agent'}
                          </Typography>
                          <Typography variant="body2">{msg.message}</Typography>
                        </Box>
                      ))}
                      {agentTyping && (
                        <Box sx={{ p: 1, fontStyle: 'italic', color: 'text.secondary' }}>
                          Agent is typing...
                        </Box>
                      )}
                    </Box>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <TextField
                        fullWidth
                        size="small"
                        placeholder="Ask the agent a question..."
                        value={chatInput}
                        onChange={(e) => setChatInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && sendChatMessage()}
                      />
                      <IconButton size="small" onClick={sendChatMessage}>
                        <SendIcon />
                      </IconButton>
                    </Box>
                  </Box>
                )}

                {/* Events Tab */}
                {activeTab === 1 && (
                  <Box sx={{ p: 2, height: 'calc(100% - 48px)', overflowY: 'auto' }}>
                    <Typography variant="h6" gutterBottom>Recent Events</Typography>
                    {recentEvents.map((event, index) => (
                      <Card key={index} sx={{ mb: 1 }}>
                        <CardContent sx={{ py: 1 }}>
                          <Typography variant="caption" color="textSecondary">
                            {new Date(event.timestamp).toLocaleTimeString()}
                          </Typography>
                          <Typography variant="body2">
                            {event.event_type.replace('_', ' ').toUpperCase()}
                          </Typography>
                          <Typography variant="caption">
                            {JSON.stringify(event.data).substring(0, 50)}...
                          </Typography>
                        </CardContent>
                      </Card>
                    ))}
                  </Box>
                )}

                {/* Feedback Tab */}
                {activeTab === 2 && (
                  <Box sx={{ p: 2, height: 'calc(100% - 48px)' }}>
                    <Button
                      fullWidth
                      variant="contained"
                      startIcon={<FeedbackIcon />}
                      onClick={() => setFeedbackDialog(true)}
                      sx={{ mb: 2 }}
                    >
                      Provide Feedback
                    </Button>
                    <Typography variant="body2" color="textSecondary">
                      Use feedback to help the agent learn from your expertise.
                    </Typography>
                  </Box>
                )}
              </Paper>
            </Grid>
          </Grid>
        </>
      )}

      {/* Feedback Dialog */}
      <Dialog open={feedbackDialog} onClose={() => setFeedbackDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Provide Training Feedback</DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 3 }}>
            <Typography gutterBottom>Overall Rating</Typography>
            <Rating
              value={feedbackRating}
              onChange={(e, newValue) => setFeedbackRating(newValue)}
              size="large"
            />
          </Box>

          <FormControl fullWidth sx={{ mb: 3 }}>
            <InputLabel>Category</InputLabel>
            <Select
              value={feedbackCategory}
              onChange={(e) => setFeedbackCategory(e.target.value)}
            >
              {feedbackCategories.map((cat) => (
                <MenuItem key={cat.value} value={cat.value}>
                  {cat.label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <TextField
            fullWidth
            multiline
            rows={4}
            label="Comments"
            placeholder="Explain what the agent did well or could improve..."
            value={feedbackComment}
            onChange={(e) => setFeedbackComment(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setFeedbackDialog(false)}>Cancel</Button>
          <Button onClick={submitFeedback} variant="contained">
            Submit Feedback
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default LiveTrainingInterface;