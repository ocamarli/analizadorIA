import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Paper,
  TextField,
  IconButton,
  Typography,
  CircularProgress,
  Divider,
  List,
  Stack,
  Tooltip,
  Chip,
  Collapse
} from '@mui/material';
import {
  Send as SendIcon,
  Code as CodeIcon,
  ContentCopy as CopyIcon,
  DataUsage as DataUsageIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import axios from 'axios';

// Editor de código
const CodeEditor = ({ language, code, readOnly = true }) => {
  return (
    <Box sx={{ position: 'relative', my: 2 }}>
      <Box sx={{
        position: 'absolute',
        top: 5,
        right: 5,
        zIndex: 1,
        bgcolor: 'background.paper',
        borderRadius: '4px'
      }}>
        <Tooltip title="Copiar código">
          <IconButton 
            size="small"
            onClick={() => {
              navigator.clipboard.writeText(code);
            }}
          >
            <CopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
      
      <SyntaxHighlighter
        language={language || 'javascript'}
        style={vscDarkPlus}
        customStyle={{
          borderRadius: '8px',
          padding: '16px'
        }}
      >
        {code}
      </SyntaxHighlighter>
    </Box>
  );
};

// Componente de mensaje
const ChatMessage = ({ message, isUser }) => {
  // Estado para controlar la expansión de la info de tokens
  const [tokenInfoExpanded, setTokenInfoExpanded] = useState(false);

  // Renderizador personalizado para bloques de código en markdown
  const components = {
    code({ node, inline, className, children, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <CodeEditor 
          language={match[1]}
          code={String(children).replace(/\n$/, '')}
        />
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    }
  };

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        mb: 2,
        maxWidth: '85%',
        alignSelf: isUser ? 'flex-end' : 'flex-start'
      }}
    >
      <Box
        sx={{
          bgcolor: isUser ? 'primary.main' : 'background.paper',
          color: isUser ? 'primary.contrastText' : 'text.primary',
          borderRadius: 2,
          p: 2,
          boxShadow: 1
        }}
      >
        {isUser ? (
          <Typography>{message.content}</Typography>
        ) : (
          <>
            <ReactMarkdown components={components}>
              {message.content}
            </ReactMarkdown>
            
            {/* Mostrar información de tokens directamente dentro del mensaje */}
            {message.token_usage && (
              <>
                <Box 
                  sx={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    cursor: 'pointer',
                    userSelect: 'none',
                    mt: 1,
                    '&:hover': { color: 'primary.main' }
                  }}
                  onClick={() => setTokenInfoExpanded(!tokenInfoExpanded)}
                >
                  <DataUsageIcon fontSize="small" sx={{ mr: 0.5 }} />
                  <Typography variant="caption" sx={{ fontWeight: 500 }}>
                    Información de uso
                  </Typography>
                  {tokenInfoExpanded ? <ExpandLessIcon fontSize="small" /> : <ExpandMoreIcon fontSize="small" />}
                </Box>

                <Collapse in={tokenInfoExpanded}>
                  <Stack direction="row" spacing={1} sx={{ mt: 1, flexWrap: 'wrap' }}>
                    <Chip
                      label={`Prompt: ${message.token_usage.prompt_tokens.toLocaleString()}`}
                      size="small"
                      color="primary"
                      variant="outlined"
                    />
                    <Chip
                      label={`Respuesta: ${message.token_usage.completion_tokens.toLocaleString()}`}
                      size="small"
                      color="secondary"
                      variant="outlined"
                    />
                    <Chip
                      label={`Total: ${message.token_usage.total_tokens.toLocaleString()}`}
                      size="small"
                      color="info"
                    />
                  </Stack>
                </Collapse>
              </>
            )}
          </>
        )}
      </Box>
    </Box>
  );
};

// Componente principal del Chatbot
const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  
  // Desplazamiento automático hacia abajo en la conversación
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };
  
  useEffect(() => {
    scrollToBottom();
  }, [messages]);
  
  // Manejar el envío de mensajes
  const handleSendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';

    try {
      const response = await axios.post(`${API_BASE_URL}/api/chatGlobal`, {
        message: input,
        history: messages
      });
      
      const assistantMessage = { 
        role: 'assistant',
        content: response.data.response,
        code_blocks: response.data.code_blocks,
        is_code_request: response.data.is_code_request,
        token_usage: response.data.token_usage // Capturar info de tokens
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error al enviar mensaje:', error);
      const errorMessage = { 
        role: 'assistant',
        content: 'Lo siento, ocurrió un error al procesar tu mensaje. Por favor, intenta nuevamente.'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };
  
  // Manejar la tecla Enter para enviar mensajes
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };
  
  return (
    <Paper 
      elevation={3}
      sx={{
        height: '80vh',
        maxWidth: '900px',
        margin: 'auto',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      {/* Encabezado */}
      <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
        <Typography variant="h6">
          Asistente IA
        </Typography>
        <Typography variant="body2">
          Pregúntame sobre los estándares o pide ayuda con tu código
        </Typography>
      </Box>
      
      <Divider />
      
      {/* Área de mensajes */}
      <Box 
        sx={{
          flexGrow: 1,
          p: 2,
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {messages.length === 0 ? (
          <Box 
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              height: '100%',
              color: 'text.secondary'
            }}
          >
            <CodeIcon sx={{ fontSize: 60, mb: 2, color: 'primary.main' }} />
            <Typography variant="h6">
              ¡Bienvenido al Asistente!
            </Typography>
            <Typography variant="body1" align="center" sx={{ mt: 1, maxWidth: '70%' }}>
              Puedo ayudarte con información sobre los estándares de código según tus necesidades.
            </Typography>
            <Stack direction="row" spacing={1} sx={{ mt: 3 }}>
              <Paper sx={{ p: 1, borderRadius: 2 }}>
                <Typography variant="body2">
                  ¿Cuáles son los estándares para desarrollo web?
                </Typography>
              </Paper>
              <Paper sx={{ p: 1, borderRadius: 2 }}>
                <Typography variant="body2">
                  Genera un componente React para una tabla de productos
                </Typography>
              </Paper>
            </Stack>
          </Box>
        ) : (
          messages.map((message, index) => (
            <ChatMessage 
              key={index}
              message={message}
              isUser={message.role === 'user'}
            />
          ))
        )}
        <div ref={messagesEndRef} />
      </Box>
      
      <Divider />
      
      {/* Área de entrada */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center' }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Escribe tu mensaje aquí..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          multiline
          maxRows={3}
          disabled={loading}
          sx={{ mr: 1 }}
        />
        <IconButton 
          color="primary"
          onClick={handleSendMessage}
          disabled={loading || !input.trim()}
          sx={{ height: 'fit-content' }}
        >
          {loading ? <CircularProgress size={24} /> : <SendIcon />}
        </IconButton>
      </Box>
    </Paper>
  );
};

export default Chatbot;