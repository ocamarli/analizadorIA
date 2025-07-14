import React, { useState, useRef } from 'react';
import {
  Box, Button, Typography, Paper, CircularProgress,
  TextField, Snackbar, Alert, Grid, Tabs, Tab, ButtonGroup
} from '@mui/material';
import { 
  Upload as UploadIcon, 
  Download as DownloadIcon,
  Send as SendIcon,
  Visibility as VisibilityIcon,
  Code as CodeIcon,
  ContentCopy as ContentCopyIcon,
  Description as DescriptionIcon
} from '@mui/icons-material';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm'; // Necesitas instalar: npm install remark-gfm

const GeneradorHistoriasTecnicas = () => {
  const [files, setFiles] = useState([]);
  const [additionalText, setAdditionalText] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState('');
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  const [viewMode, setViewMode] = useState(0); // 0: rendered, 1: raw
  
  const fileInputRef = useRef(null);
  
  // Manejo de archivos
  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const validFiles = selectedFiles.filter(file => 
      file.type === 'application/pdf' || 
      file.name.toLowerCase().endsWith('.md') ||
      file.name.toLowerCase().endsWith('.markdown') ||
      file.name.toLowerCase().endsWith('.xml') ||
      file.name.toLowerCase().endsWith('.drawio') ||
      file.name.toLowerCase().endsWith('.mmd') ||
      file.name.toLowerCase().endsWith('.txt') ||
      file.type === 'text/xml' ||
      file.type === 'application/xml' ||
      file.type === 'text/plain'
    );
    
    if (validFiles.length !== selectedFiles.length) {
      showNotification('Solo archivos PDF, Markdown, XML/DrawIO, Mermaid y TXT', 'warning');
    }
    
    setFiles(validFiles);
  };
  
  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    const droppedFiles = Array.from(event.dataTransfer.files);
    const validFiles = droppedFiles.filter(file => 
      file.type === 'application/pdf' || 
      file.name.toLowerCase().endsWith('.md') ||
      file.name.toLowerCase().endsWith('.markdown') ||
      file.name.toLowerCase().endsWith('.xml') ||
      file.name.toLowerCase().endsWith('.drawio') ||
      file.name.toLowerCase().endsWith('.mmd') ||
      file.name.toLowerCase().endsWith('.txt') ||
      file.type === 'text/xml' ||
      file.type === 'application/xml' ||
      file.type === 'text/plain'
    );
    
    setFiles(validFiles);
  };
  
  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };
  
  // Generar historias técnicas
  const generateTechnicalStories = async () => {
    // Validar que haya al menos archivos o texto
    if (files.length === 0 && !additionalText.trim()) {
      showNotification('Selecciona archivos o ingresa especificaciones técnicas', 'warning');
      return;
    }
    
    setIsProcessing(true);
    setResponse('');
    
    try {
      const formData = new FormData();
      
      // Agregar archivos si existen
      files.forEach(file => {
        formData.append('files', file);
      });
      
      // Agregar texto adicional
      formData.append('additional_text', additionalText.trim());
      
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';
      const apiResponse = await fetch(`${API_BASE_URL}/api/generar-historias-tecnicas`, {
        method: 'POST',
        body: formData,
      });
      
      if (!apiResponse.ok) {
        const errorData = await apiResponse.json();
        throw new Error(errorData.error || 'Error en el servidor');
      }
      
      const result = await apiResponse.json();
      setResponse(result.respuesta);
      showNotification('¡Historias técnicas generadas!', 'success');
      
    } catch (error) {
      console.error('Error:', error);
      showNotification(`Error: ${error.message}`, 'error');
    } finally {
      setIsProcessing(false);
    }
  };
  
  // Descargar respuesta como archivo Markdown
  const downloadMarkdown = () => {
    if (!response) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const blob = new Blob([response], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Historias_Tecnicas_${new Date().toISOString().split('T')[0]}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Archivo Markdown descargado', 'success');
  };

  // Función mejorada para convertir markdown a HTML con mejor manejo de tablas
  const markdownToHtml = (markdownText) => {
    let htmlContent = markdownText;
    
    // Procesar tablas de markdown - patrón más robusto
    const tableRegex = /\|(.+)\|\s*\n\|(\s*:?-+:?\s*\|)+\s*\n((\|.+\|\s*\n)*)/gm;
    htmlContent = htmlContent.replace(tableRegex, (match, header, separator, rows) => {
      // Procesar headers
      const headerCells = header.split('|')
        .map(cell => cell.trim())
        .filter(cell => cell)
        .map(cell => `<th>${cell}</th>`)
        .join('');
      
      // Procesar filas
      const rowsHtml = rows.trim().split('\n')
        .map(row => {
          const cells = row.split('|')
            .map(cell => cell.trim())
            .filter(cell => cell)
            .map(cell => `<td>${cell}</td>`)
            .join('');
          return `<tr>${cells}</tr>`;
        })
        .join('');
      
      return `<table border="1" style="border-collapse: collapse; width: 100%; margin: 10px 0;">
        <thead><tr>${headerCells}</tr></thead>
        <tbody>${rowsHtml}</tbody>
      </table>`;
    });
    
    // Resto de conversiones markdown
    htmlContent = htmlContent
      // Encabezados
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // Texto en negrita y cursiva
      .replace(/\*\*\*(.*?)\*\*\*/gim, '<strong><em>$1</em></strong>')
      .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/gim, '<em>$1</em>')
      // Enlaces
      .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2">$1</a>')
      // Código inline
      .replace(/`([^`]+)`/gim, '<code>$1</code>')
      // Bloques de código
      .replace(/```[\s\S]*?```/gim, (match) => {
        const code = match.replace(/```/g, '').trim();
        return `<pre><code>${code}</code></pre>`;
      })
      // Listas no ordenadas
      .replace(/^\* (.+$)/gim, '<li>$1</li>')
      .replace(/^- (.+$)/gim, '<li>$1</li>')
      // Listas ordenadas
      .replace(/^\d+\. (.+$)/gim, '<li>$1</li>')
      // Líneas horizontales
      .replace(/^---$/gim, '<hr>')
      // Párrafos
      .replace(/\n\n/gim, '</p><p>')
      // Saltos de línea
      .replace(/\n/gim, '<br>');

    // Envolver listas en tags ul/ol
    if (htmlContent.includes('<li>')) {
      // Detectar si es lista ordenada o no ordenada y envolver apropiadamente
      htmlContent = htmlContent.replace(/(<li>.*?<\/li>)/gis, '<ul>$1</ul>');
      htmlContent = htmlContent.replace(/<\/ul><ul>/gim, '');
    }

    // Envolver en párrafos
    htmlContent = '<p>' + htmlContent + '</p>';
    
    return htmlContent;
  };

  // Descargar respuesta como archivo Word mejorado
  const downloadWord = () => {
    if (!response) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const htmlContent = markdownToHtml(response);

    // Plantilla HTML para Word con estilos mejorados para tablas
    const wordContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>Historias Técnicas</title>
        <style>
          body { 
            font-family: Arial, sans-serif; 
            margin: 40px; 
            line-height: 1.6; 
            color: #333;
          }
          h1 { 
            color: #2c3e50; 
            border-bottom: 2px solid #3498db; 
            padding-bottom: 10px;
            page-break-after: avoid;
          }
          h2 { 
            color: #34495e; 
            margin-top: 30px;
            page-break-after: avoid;
          }
          h3 { 
            color: #7f8c8d;
            page-break-after: avoid;
          }
          code { 
            background-color: #f8f9fa; 
            padding: 2px 4px; 
            border-radius: 3px; 
            font-family: 'Courier New', monospace; 
          }
          pre {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
            border-left: 4px solid #3498db;
          }
          ul, ol { 
            padding-left: 20px; 
          }
          li { 
            margin-bottom: 5px; 
          }
          p { 
            margin-bottom: 15px; 
            text-align: justify;
          }
          strong { 
            color: #2c3e50; 
          }
          table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            page-break-inside: avoid;
          }
          th, td {
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
            vertical-align: top;
          }
          th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #2c3e50;
          }
          tr:nth-child(even) {
            background-color: #f9f9f9;
          }
          hr {
            border: none;
            height: 2px;
            background-color: #3498db;
            margin: 30px 0;
          }
          a {
            color: #3498db;
            text-decoration: none;
          }
          a:hover {
            text-decoration: underline;
          }
          @media print {
            table {
              page-break-inside: auto;
            }
            tr {
              page-break-inside: avoid;
              page-break-after: auto;
            }
          }
        </style>
      </head>
      <body>
        ${htmlContent}
      </body>
      </html>
    `;
    
    const blob = new Blob([wordContent], { type: 'application/msword;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `Historias_Tecnicas_${new Date().toISOString().split('T')[0]}.doc`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Archivo Word descargado', 'success');
  };

  // Copiar contenido al portapapeles
  const copyToClipboard = async () => {
    if (!response) {
      showNotification('No hay contenido para copiar', 'warning');
      return;
    }

    try {
      await navigator.clipboard.writeText(response);
      showNotification('Contenido copiado al portapapeles', 'success');
    } catch (err) {
      console.error('Error al copiar:', err);
      showNotification('Error al copiar al portapapeles', 'error');
    }
  };
  
  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  const handleCloseNotification = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };
  
  const handleViewModeChange = (event, newValue) => {
    setViewMode(newValue);
  };
  
  return (
    <Box sx={{ p: 3, maxWidth: 800, margin: '0 auto' }}>
      <Typography variant="h4" gutterBottom align="center">
        Generador de Historias Técnicas
      </Typography>
      
      <Grid container spacing={3}>
        {/* Carga de archivos */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Historias de Usuario y Análisis Técnico
            </Typography>
            
            <Paper
              elevation={0}
              sx={{
                p: 4,
                border: '2px dashed #ccc',
                textAlign: 'center',
                cursor: 'pointer',
                mb: 2,
                '&:hover': { borderColor: 'primary.main' }
              }}
              onClick={() => fileInputRef.current.click()}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
            >
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: 'none' }}
                multiple
                accept=".pdf,.md,.markdown,.xml,.drawio,.mmd,.txt"
              />
              <UploadIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
              <Typography variant="body1" gutterBottom>
                Arrastra archivos o haz clic para seleccionar
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Formatos: PDF, Markdown (.md), XML/DrawIO, Mermaid (.mmd), TXT
              </Typography>
            </Paper>
            
            {files.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Archivos seleccionados:
                </Typography>
                {files.map((file, index) => (
                  <Typography key={index} variant="body2" sx={{ ml: 2 }}>
                    • {file.name}
                  </Typography>
                ))}
              </Box>
            )}
          </Paper>
        </Grid>
        
        {/* Caja de texto adicional */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Especificaciones Técnicas Adicionales (Opcional)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Define estándares de código, patrones específicos, APIs requeridas, y cualquier especificación técnica adicional.
            </Typography>
            
            <TextField
              fullWidth
              multiline
              rows={8}
              variant="outlined"
              placeholder="Ejemplo:
ESTÁNDARES DE CÓDIGO:
- TypeScript strict mode habilitado
- ESLint + Prettier configurados
- Cobertura de tests >90% para lógica crítica
- Conventional Commits para mensajes de git

PATRONES ARQUITECTÓNICOS:
- Repository pattern para acceso a datos
- CQRS para separación de comandos y consultas
- Event-driven architecture para notificaciones
- Factory pattern para creación de servicios

APIS ESPECÍFICAS:
- REST APIs con OpenAPI/Swagger documentation
- GraphQL para consultas complejas del frontend
- WebSockets para notificaciones en tiempo real
- Rate limiting: 100 requests/minuto por usuario

TECNOLOGÍAS OBLIGATORIAS:
- Frontend: React 18 + TypeScript + Material-UI
- Backend: Node.js + Express + Prisma ORM
- Testing: Jest + React Testing Library + Supertest
- DevOps: Docker + GitHub Actions + AWS ECS

REQUERIMIENTOS NO FUNCIONALES:
- Performance: <300ms response time para APIs
- Seguridad: JWT authentication + RBAC authorization
- Scalability: Soporte para 10k usuarios concurrentes
- Monitoring: Prometheus + Grafana + CloudWatch..."
              value={additionalText}
              onChange={(e) => setAdditionalText(e.target.value)}
              sx={{
                '& .MuiInputBase-input': {
                  fontFamily: 'monospace',
                  fontSize: '0.875rem'
                }
              }}
            />
            
            {additionalText.trim() && (
              <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                Caracteres: {additionalText.length}
              </Typography>
            )}
          </Paper>
        </Grid>
        
        {/* Botón generar */}
        <Grid item xs={12}>
          <Button
            variant="contained"
            size="large"
            fullWidth
            onClick={generateTechnicalStories}
            disabled={isProcessing || (files.length === 0 && !additionalText.trim())}
            startIcon={isProcessing ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
            sx={{ py: 1.5 }}
          >
            {isProcessing ? 'Generando...' : 'Generar Historias Técnicas'}
          </Button>
        </Grid>
        
        {/* Respuesta */}
        {response && (
          <Grid item xs={12}>
            <Paper sx={{ p: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Historias Técnicas Generadas
                </Typography>
                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    startIcon={<ContentCopyIcon />}
                    onClick={copyToClipboard}
                    size="small"
                  >
                    Copiar
                  </Button>
                  <ButtonGroup variant="outlined" size="small">
                    <Button
                      startIcon={<DownloadIcon />}
                      onClick={downloadMarkdown}
                    >
                      MD
                    </Button>
                    <Button
                      startIcon={<DescriptionIcon />}
                      onClick={downloadWord}
                    >
                      Word
                    </Button>
                  </ButtonGroup>
                </Box>
              </Box>
              
              {/* Tabs para cambiar entre vista renderizada y código */}
              <Tabs value={viewMode} onChange={handleViewModeChange} sx={{ mb: 2 }}>
                <Tab 
                  icon={<VisibilityIcon />} 
                  label="Vista Renderizada" 
                  iconPosition="start"
                />
                <Tab 
                  icon={<CodeIcon />} 
                  label="Código Markdown" 
                  iconPosition="start"
                />
              </Tabs>
              
              {viewMode === 0 ? (
                // Vista renderizada con react-markdown y soporte para tablas
                <Paper
                  variant="outlined"
                  sx={{
                    p: 3,
                    maxHeight: '600px',
                    overflow: 'auto',
                    backgroundColor: '#fafafa',
                    '& h1, & h2, & h3, & h4, & h5, & h6': {
                      color: 'primary.main',
                      marginTop: 2,
                      marginBottom: 1
                    },
                    '& p': {
                      marginBottom: 1,
                      lineHeight: 1.6
                    },
                    '& ul, & ol': {
                      paddingLeft: 2
                    },
                    '& li': {
                      marginBottom: 0.5
                    },
                    '& code': {
                      backgroundColor: '#e0e0e0',
                      padding: '2px 4px',
                      borderRadius: 1,
                      fontSize: '0.875rem'
                    },
                    '& pre': {
                      backgroundColor: '#f5f5f5',
                      padding: 2,
                      borderRadius: 1,
                      overflow: 'auto',
                      '& code': {
                        backgroundColor: 'transparent',
                        padding: 0
                      }
                    },
                    '& blockquote': {
                      borderLeft: '4px solid #ccc',
                      paddingLeft: 2,
                      marginLeft: 0,
                      fontStyle: 'italic',
                      color: 'text.secondary'
                    },
                    // Estilos específicos para tablas
                    '& table': {
                      width: '100%',
                      borderCollapse: 'collapse',
                      marginTop: 2,
                      marginBottom: 2,
                      backgroundColor: 'white',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
                    },
                    '& th, & td': {
                      border: '1px solid #ddd',
                      padding: '12px',
                      textAlign: 'left',
                      verticalAlign: 'top'
                    },
                    '& th': {
                      backgroundColor: '#f8f9fa',
                      fontWeight: 'bold',
                      color: '#2c3e50'
                    },
                    '& tbody tr:nth-of-type(even)': {
                      backgroundColor: '#f9f9f9'
                    },
                    '& tbody tr:hover': {
                      backgroundColor: '#f1f3f4'
                    }
                  }}
                >
                  <Markdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // Personalizar componente de tabla si es necesario
                      table: ({children, ...props}) => (
                        <table style={{
                          width: '100%',
                          borderCollapse: 'collapse',
                          margin: '16px 0'
                        }} {...props}>
                          {children}
                        </table>
                      )
                    }}
                  >
                    {response}
                  </Markdown>
                </Paper>
              ) : (
                // Vista de código markdown
                <TextField
                  fullWidth
                  multiline
                  rows={20}
                  value={response}
                  variant="outlined"
                  InputProps={{
                    readOnly: true,
                    style: { 
                      fontFamily: 'monospace', 
                      fontSize: '0.875rem',
                      whiteSpace: 'pre-wrap'
                    }
                  }}
                />
              )}
            </Paper>
          </Grid>
        )}
      </Grid>
      
      {/* Notificaciones */}
      <Snackbar
        open={notification.open}
        autoHideDuration={4000}
        onClose={handleCloseNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseNotification} severity={notification.severity}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default GeneradorHistoriasTecnicas;