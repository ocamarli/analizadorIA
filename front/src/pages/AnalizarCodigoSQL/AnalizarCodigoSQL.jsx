import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Button,
  Container,
  TextField,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Tooltip,
  Chip,
  Stack,
  Collapse,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  Badge,
  Grid,
  LinearProgress,
  ButtonGroup,
  Snackbar
} from '@mui/material';
import {
  FolderOpen as FolderOpenIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  FileCopy as FileCopyIcon,
  InsertDriveFile as FileIcon,
  Folder as FolderIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowRight as KeyboardArrowRightIcon,
  Assessment as AssessmentIcon,
  Storage as StorageIcon,
  Assignment as AssignmentIcon,
  CloudDone as CloudDoneIcon,
  Delete as DeleteIcon,
  Upload as UploadIcon,
  Download as DownloadIcon,
  Visibility as VisibilityIcon,
  ContentCopy as ContentCopyIcon
} from '@mui/icons-material';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import axios from 'axios';
import { io } from 'socket.io-client';

// Definimos algunos estilos
const styles = {
  container: {
    mt: 4,
    mb: 4
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    mb: 3
  },
  headerIcon: {
    mr: 2,
    color: 'primary.main',
    fontSize: 40
  },
  inputSection: {
    mb: 4
  },
  folderSelector: {
    border: '2px dashed #ccc',
    borderRadius: 2,
    p: 4,
    textAlign: 'center',
    transition: 'border-color 0.3s',
    '&:hover': {
      borderColor: 'primary.main'
    }
  },
  filePreview: {
    mt: 2,
    maxHeight: 300,
    overflow: 'auto',
    border: '1px solid #e0e0e0',
    borderRadius: 1,
    p: 2
  },
  treeItem: {
    py: 0.5
  },
  nestedTreeItem: {
    pl: 4
  },
  loadingContainer: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    flexDirection: 'column',
    height: 200
  },
  statsCard: {
    mb: 3
  },
  treeViewContainer: {
    maxHeight: 400,
    overflow: 'auto',
    border: '1px solid #e0e0e0',
    borderRadius: 1,
    p: 1
  },
  summaryCard: {
    mb: 3,
    p: 2,
    bgcolor: 'primary.light',
    color: 'primary.contrastText'
  },
  tabPanel: {
    mt: 2
  }
};

// Componente para Panel de pestañas
function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analysis-tabpanel-${index}`}
      aria-labelledby={`analysis-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={styles.tabPanel}>
          {children}
        </Box>
      )}
    </div>
  );
}

// Componente para visualizar el árbol de directorios
const TreeView = ({ data }) => {
  const [expanded, setExpanded] = useState({});

  const toggleExpand = (path) => {
    setExpanded(prev => ({
      ...prev,
      [path]: !prev[path]
    }));
  };

  const renderTree = (node, path = '') => {
    const currentPath = path ? `${path}/${node.name}` : node.name;
    const isExpanded = expanded[currentPath] || false;
    const hasChildren = node.children && node.children.length > 0;

    return (
      <Box key={currentPath}>
        <ListItem
          sx={styles.treeItem}
          dense
          secondaryAction={
            hasChildren && (
              <IconButton edge="end" onClick={() => toggleExpand(currentPath)} size="small">
                {isExpanded ? <KeyboardArrowDownIcon /> : <KeyboardArrowRightIcon />}
              </IconButton>
            )
          }
        >
          <ListItemIcon>
            {node.type === 'folder' ? <FolderIcon color="primary" /> : <FileIcon color="info" />}
          </ListItemIcon>
          <ListItemText 
            primary={node.name}
            secondary={
              <Box>
                {node.type === 'file' && node.extension && (
                  <Chip label={node.extension} size="small" variant="outlined" sx={{ mr: 1 }} />
                )}
                {node.path && (
                  <Typography variant="caption" color="text.secondary">
                    {node.path}
                  </Typography>
                )}
              </Box>
            }
            primaryTypographyProps={{
              variant: 'body2',
              fontWeight: node.type === 'folder' ? 'medium' : 'normal'
            }}
          />
        </ListItem>
        
        {hasChildren && (
          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
            <List component="div" disablePadding sx={styles.nestedTreeItem}>
              {node.children.map(child => renderTree(child, currentPath))}
            </List>
          </Collapse>
        )}
      </Box>
    );
  };

  return (
    <Box sx={styles.treeViewContainer}>
      <List dense>
        {renderTree(data)}
      </List>
    </Box>
  );
};

// Componente para mostrar estadísticas del proyecto
const ProjectStats = ({ stats, codeAnalysis }) => {
  return (
    <Card sx={styles.statsCard}>
      <CardContent>
        <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
          <AssessmentIcon sx={{ mr: 1 }} /> Estadísticas del Proyecto de Base de Datos
        </Typography>
        
        <TableContainer>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell component="th" scope="row">Tipo:</TableCell>
                <TableCell align="right">
                  <Chip label={codeAnalysis?.language || 'SQL/Database'} color="primary" size="small" />
                </TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Total de archivos:</TableCell>
                <TableCell align="right">{stats.total_files}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos analizados:</TableCell>
                <TableCell align="right">{stats.analyzed_files}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Total de líneas:</TableCell>
                <TableCell align="right">{stats.total_lines?.toLocaleString()}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos SQL:</TableCell>
                <TableCell align="right">{stats.sql_files || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos DDL:</TableCell>
                <TableCell align="right">{stats.ddl_files || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos de procedimientos:</TableCell>
                <TableCell align="right">{stats.procedure_files || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Tablas encontradas:</TableCell>
                <TableCell align="right">{stats.total_tables || codeAnalysis?.total_tables || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Procedimientos encontrados:</TableCell>
                <TableCell align="right">{stats.total_procedures || codeAnalysis?.total_procedures || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Funciones encontradas:</TableCell>
                <TableCell align="right">{stats.total_functions || codeAnalysis?.total_functions || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Vistas encontradas:</TableCell>
                <TableCell align="right">{stats.total_views || codeAnalysis?.total_views || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Triggers encontrados:</TableCell>
                <TableCell align="right">{stats.total_triggers || codeAnalysis?.total_triggers || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Índices encontrados:</TableCell>
                <TableCell align="right">{stats.total_indexes || codeAnalysis?.total_indexes || 0}</TableCell>
              </TableRow>
            </TableBody>
          </Table>
        </TableContainer>
        
        {stats.extensions && Object.keys(stats.extensions).length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Distribución por extensión:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {Object.entries(stats.extensions).map(([ext, count]) => (
                <Chip
                  key={ext}
                  label={`${ext}: ${count}`}
                  size="small"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              ))}
            </Stack>
          </Box>
        )}

        {codeAnalysis?.database_engines && codeAnalysis.database_engines.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Motores de base de datos detectados:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {codeAnalysis.database_engines.map((engine, index) => (
                <Chip
                  key={index}
                  label={engine}
                  size="small"
                  color="secondary"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              ))}
            </Stack>
          </Box>
        )}

        {codeAnalysis?.schemas_found && codeAnalysis.schemas_found.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Esquemas encontrados:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {codeAnalysis.schemas_found.map((schema, index) => (
                <Chip
                  key={index}
                  label={schema}
                  size="small"
                  color="info"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              ))}
            </Stack>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

// Componente para mostrar resumen del análisis
const AnalysisSummary = ({ summary, timestamp }) => {
  return (
    <Paper sx={styles.summaryCard}>
      <Grid container spacing={2} alignItems="center">
        <Grid item>
          <CloudDoneIcon sx={{ fontSize: 40 }} />
        </Grid>
        <Grid item xs>
          <Typography variant="h6" gutterBottom>
            Análisis de base de datos completado exitosamente
          </Typography>
          <Typography variant="body2">
            {summary?.upload_method === 'zip_upload' ? 'Método: Archivo ZIP subido' : 'Método: Selección directa de carpeta'}
          </Typography>
          <Typography variant="body2">
            Análisis realizado el: {new Date().toLocaleString()}
          </Typography>
          {summary?.consolidation_applied && (
            <Typography variant="body2" color="success.main">
              ✓ Consolidación automática aplicada
            </Typography>
          )}
          {summary?.retry_info?.rate_limiting_encountered && (
            <Typography variant="body2" color="warning.main">
              ⚠ Rate limiting detectado ({summary.retry_info.total_retries_used} reintentos)
            </Typography>
          )}
        </Grid>
        <Grid item>
          <Box sx={{ display: 'flex', gap: 2 }}>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary.contrastText">
                {summary?.files_analyzed || 0}
              </Typography>
              <Typography variant="caption">
                Archivos analizados
              </Typography>
            </Box>
            <Box sx={{ textAlign: 'center' }}>
              <Typography variant="h4" color="primary.contrastText">
                {summary?.total_lines_analyzed?.toLocaleString() || 0}
              </Typography>
              <Typography variant="caption">
                Líneas analizadas
              </Typography>
            </Box>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

// Componente para mostrar contenido con vista renderizada y código
const ContentViewer = ({ content, title, filename, viewMode, setViewMode }) => {
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });

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

  // Función para descargar contenido como archivo Markdown
  const downloadAsMarkdown = () => {
    if (!content) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename || `documento_${new Date().toISOString().split('T')[0]}.md`;
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
      htmlContent = htmlContent.replace(/(<li>.*?<\/li>)/gis, '<ul>$1</ul>');
      htmlContent = htmlContent.replace(/<\/ul><ul>/gim, '');
    }

    // Envolver en párrafos
    htmlContent = '<p>' + htmlContent + '</p>';
    
    return htmlContent;
  };

  // Descargar respuesta como archivo Word mejorado
  const downloadWord = () => {
    if (!content) {
      showNotification('No hay contenido para descargar', 'warning');
      return;
    }
    
    const htmlContent = markdownToHtml(content);

    const wordContent = `
      <!DOCTYPE html>
      <html>
      <head>
        <meta charset="utf-8">
        <title>${title || 'Documento'}</title>
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
    link.download = (filename || 'documento').replace('.md', '.doc');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    showNotification('Archivo Word descargado', 'success');
  };

  // Copiar contenido al portapapeles
  const copyToClipboard = async () => {
    if (!content) {
      showNotification('No hay contenido para copiar', 'warning');
      return;
    }

    try {
      await navigator.clipboard.writeText(content);
      showNotification('Contenido copiado al portapapeles', 'success');
    } catch (err) {
      console.error('Error al copiar:', err);
      showNotification('Error al copiar al portapapeles', 'error');
    }
  };

  const handleViewModeChange = (event, newValue) => {
    setViewMode(newValue);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h5">
          {title}
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
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
              onClick={downloadAsMarkdown}
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
            {content}
          </Markdown>
        </Paper>
      ) : (
        // Vista de código markdown
        <TextField
          fullWidth
          multiline
          rows={20}
          value={content}
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

const AnalizarCodigoSQL = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [projectName, setProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userStories, setUserStories] = useState('');
  const [defAnalysis, setDefAnalysis] = useState('');
  const [analyzedFiles, setAnalyzedFiles] = useState([]);
  const [directoryTree, setDirectoryTree] = useState(null);
  const [projectStats, setProjectStats] = useState(null);
  const [codeAnalysis, setCodeAnalysis] = useState(null);
  const [summary, setSummary] = useState(null);
  const [timestamp, setTimestamp] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [folderStructure, setFolderStructure] = useState(null);
  const [viewMode, setViewMode] = useState(0); // 0: rendered, 1: raw

  // Estados para progreso por chunks - SIMPLIFICADO
  const [processingStatus, setProcessingStatus] = useState('');
  const [progressInfo, setProgressInfo] = useState({
    percentage: 0,
    currentChunk: 0,
    totalChunks: 0,
    phase: ''
  });
  const [sessionId, setSessionId] = useState(null);
  const [socket, setSocket] = useState(null);

  // Extensiones permitidas
  const allowedExtensions = ['.sql', '.ddl', '.dml', '.pgsql', '.psql', '.mysql', '.plsql', '.proc', 
                            '.sp', '.fn', '.udf', '.view', '.trigger', '.idx', '.schema', '.dump',
                            '.backup', '.db', '.sqlite', '.sqlite3', '.dbf', '.mdb', '.accdb'];

  // Configurar WebSocket - MEJORADO
  useEffect(() => {
    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';
    const newSocket = io(API_BASE_URL);
    
    newSocket.on('analysis_progress', (data) => {
      console.log('Progreso recibido:', data); // Para debugging
      
      if (data.session_id === sessionId) {
        // Calcular progreso basado en chunks si están disponibles
        let calculatedProgress = data.progress || 0;
        
        if (data.total_chunks > 0 && data.current_chunk > 0) {
          // Progreso base: 20% para preparación inicial
          const baseProgress = 20;
          // Progreso por chunk: 70% dividido entre los chunks
          const chunkProgress = (data.current_chunk / data.total_chunks) * 70;
          // Progreso final: 10% para consolidación
          calculatedProgress = baseProgress + chunkProgress;
          
          // Si es el último chunk y la fase es consolidación, añadir progreso final
          if (data.current_chunk === data.total_chunks && data.phase?.toLowerCase().includes('consolidación')) {
            calculatedProgress = 95;
          }
        }
        
        setProgressInfo({
          percentage: Math.min(calculatedProgress, 100),
          currentChunk: data.current_chunk || 0,
          totalChunks: data.total_chunks || 0,
          phase: data.phase || ''
        });
        
        // Actualizar status con información más simple
        if (data.total_chunks > 1) {
          setProcessingStatus(`${data.phase} (${data.current_chunk}/${data.total_chunks} secciones)`);
        } else {
          setProcessingStatus(data.phase || 'Procesando...');
        }
      }
    });

    // Manejar finalización del análisis
    newSocket.on('analysis_complete', (data) => {
      if (data.session_id === sessionId) {
        setProgressInfo(prev => ({ ...prev, percentage: 100 }));
        setProcessingStatus('Análisis completado');
      }
    });

    // Manejar errores
    newSocket.on('analysis_error', (data) => {
      if (data.session_id === sessionId) {
        setProcessingStatus(`Error: ${data.error}`);
      }
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [sessionId]);

  // Función para verificar si un archivo es permitido
  const isAllowedFile = (filename) => {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return allowedExtensions.includes(ext) || 
           ['schema.sql', 'init.sql', 'migrations.sql', 'procedures.sql'].includes(filename);
  };

  // Función para construir estructura de carpetas a partir de archivos
  const buildFolderStructure = (files) => {
    const structure = { name: projectName || 'Proyecto de Base de Datos', type: 'folder', children: [], files: [] };
    
    files.forEach(file => {
      const pathParts = file.webkitRelativePath.split('/');
      let current = structure;
      
      // Navegar/crear estructura de carpetas
      for (let i = 0; i < pathParts.length - 1; i++) {
        const folderName = pathParts[i];
        let folder = current.children.find(child => child.name === folderName && child.type === 'folder');
        
        if (!folder) {
          folder = { name: folderName, type: 'folder', children: [], files: [] };
          current.children.push(folder);
        }
        current = folder;
      }
      
      // Agregar archivo a la carpeta actual
      const fileName = pathParts[pathParts.length - 1];
      if (isAllowedFile(fileName)) {
        const fileObj = {
          name: fileName,
          type: 'file',
          extension: '.' + fileName.split('.').pop().toLowerCase(),
          path: file.webkitRelativePath,
          file: file
        };
        current.children.push(fileObj);
        current.files.push(fileObj);
      }
    });

    return structure;
  };

  // Manejar selección de carpeta
  const handleFolderSelect = (event) => {
    const files = Array.from(event.target.files);
    
    if (files.length === 0) {
      setError('No se seleccionaron archivos');
      return;
    }

    // Filtrar solo archivos permitidos
    const validFiles = files.filter(file => isAllowedFile(file.name));
    
    if (validFiles.length === 0) {
      setError('No se encontraron archivos de base de datos en la carpeta seleccionada');
      return;
    }

    // Construir estructura de carpetas
    const structure = buildFolderStructure(validFiles);
    
    setSelectedFiles(validFiles);
    setFolderStructure(structure);
    setError(null);

    // Auto-detectar nombre del proyecto si no está establecido
    if (!projectName && validFiles.length > 0) {
      const firstPath = validFiles[0].webkitRelativePath;
      const rootFolder = firstPath.split('/')[0];
      setProjectName(rootFolder);
    }
  };

  // Crear ZIP en el cliente
  const createZipFromFiles = async (files) => {
    // Importar JSZip dinámicamente (necesitarás instalarlo: npm install jszip)
    const JSZip = (await import('jszip')).default;
    const zip = new JSZip();

    for (const file of files) {
      const relativePath = file.webkitRelativePath || file.name;
      zip.file(relativePath, file);
    }

    return await zip.generateAsync({ type: 'blob' });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (selectedFiles.length === 0) {
      setError('Por favor, selecciona una carpeta con archivos de base de datos');
      return;
    }

    if (!projectName.trim()) {
      setError('Por favor, ingresa un nombre para el proyecto de base de datos');
      return;
    }

    setLoading(true);
    setError(null);
    setProgressInfo({ percentage: 0, currentChunk: 0, totalChunks: 0, phase: '' });
    setProcessingStatus('Iniciando análisis...');

    try {
      // Crear ZIP automáticamente
      setProgressInfo(prev => ({ ...prev, percentage: 5 }));
      setProcessingStatus('Preparando archivos...');
      const zipBlob = await createZipFromFiles(selectedFiles);
      
      setProgressInfo(prev => ({ ...prev, percentage: 10 }));
      setProcessingStatus('Creando archivo ZIP...');
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setProgressInfo(prev => ({ ...prev, percentage: 15 }));
      setProcessingStatus('Subiendo archivo...');
      
      const formData = new FormData();
      formData.append('zip_file', zipBlob, `${projectName}.zip`);
      formData.append('project_name', projectName.trim());

      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';

      // Generar session_id único para tracking
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      setSessionId(newSessionId);
      formData.append('session_id', newSessionId);

      const response = await axios.post(`${API_BASE_URL}/api/analizarCodigoSQL/zip`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const uploadPercent = Math.round((progressEvent.loaded * 5) / progressEvent.total);
          setProgressInfo(prev => ({ ...prev, percentage: 15 + uploadPercent })); // Máximo 20%
        }
      });

      // El resto del progreso será manejado por WebSocket
      if (response.data.success) {
        // Asegurar que llegamos al 100% al final
        setProgressInfo(prev => ({ ...prev, percentage: 100 }));
        setProcessingStatus('Análisis completado exitosamente');
        
        setUserStories(response.data.user_stories || '');
        setDefAnalysis(response.data.def_analysis || '');
        setAnalyzedFiles(response.data.analyzed_files || []);
        setDirectoryTree(response.data.directory_tree || folderStructure);
        setProjectStats(response.data.project_stats || null);
        setCodeAnalysis(response.data.code_analysis || null);
        setSummary(response.data.summary || null);
        setTimestamp(response.data.timestamp || '');
      }
      
    } catch (err) {
      console.error("Error completo:", err);
      setError(err.response?.data?.error || err.message || 'Ocurrió un error al analizar la base de datos');
      setProgressInfo(prev => ({ ...prev, percentage: 0 }));
      setProcessingStatus('');
    } finally {
      setLoading(false);
      // Reset después de 3 segundos
      setTimeout(() => {
        setProgressInfo({ percentage: 0, currentChunk: 0, totalChunks: 0, phase: '' });
        setProcessingStatus('');
        setSessionId(null);
      }, 3000);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const clearSelection = () => {
    setSelectedFiles([]);
    setFolderStructure(null);
    setProjectName('');
    setError(null);
  };

  return (
    <Container maxWidth="lg" sx={styles.container}>
      {/* Cabecera */}
      <Box sx={styles.header}>
        <CodeIcon sx={styles.headerIcon} />
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Análisis de Bases de Datos - Cloud
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Selecciona una carpeta con archivos SQL y genera historias de usuario y análisis DEF utilizando IA
          </Typography>
        </Box>
      </Box>

      {/* Sección de entrada */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Seleccionar carpeta con archivos de base de datos
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit} sx={styles.inputSection}>
          {/* Nombre del proyecto */}
          <TextField
            fullWidth
            label="Nombre del proyecto de base de datos"
            variant="outlined"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Mi Base de Datos"
            sx={{ mb: 3 }}
            required
          />

          {/* Selector de carpeta */}
          <Box sx={styles.folderSelector}>
            <FolderOpenIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Seleccionar carpeta con archivos SQL
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Haz clic para seleccionar una carpeta que contenga archivos SQL, DDL, procedimientos, etc.
            </Typography>
            
            <Button
              variant="outlined"
              component="label"
              startIcon={<FolderOpenIcon />}
              size="large"
            >
              Seleccionar Carpeta SQL
              <input
                type="file"
                hidden
                webkitdirectory=""
                directory=""
                multiple
                onChange={handleFolderSelect}
              />
            </Button>
          </Box>

          {/* Vista previa de archivos seleccionados */}
          {folderStructure && (
            <Paper variant="outlined" sx={styles.filePreview}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6">
                  Estructura de la carpeta ({selectedFiles.length} archivos encontrados)
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={<DeleteIcon />}
                  onClick={clearSelection}
                  size="small"
                >
                  Limpiar
                </Button>
              </Box>
              <TreeView data={folderStructure} />
            </Paper>
          )}

          {/* Progreso de procesamiento SIMPLIFICADO */}
          {loading && progressInfo.percentage > 0 && (
            <Box sx={{ mt: 3, mb: 2 }}>
              {/* Header del progreso */}
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                  {processingStatus}
                </Typography>
                <Typography variant="body2" color="primary" fontWeight="bold">
                  {Math.round(progressInfo.percentage)}%
                </Typography>
              </Box>
              
              {/* Barra de progreso */}
              <LinearProgress 
                variant="determinate" 
                value={progressInfo.percentage} 
                sx={{ 
                  height: 8, 
                  borderRadius: 4,
                  backgroundColor: 'grey.200',
                  '& .MuiLinearProgress-bar': {
                    borderRadius: 4,
                    transition: 'transform 0.8s ease',
                    backgroundColor: progressInfo.percentage >= 100 ? '#4caf50' : '#2196f3'
                  }
                }}
              />
              
              {/* Información adicional solo si hay chunks */}
              {progressInfo.totalChunks > 1 && (
                <Box sx={{ mt: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="caption" color="text.secondary">
                    Procesando en {progressInfo.totalChunks} secciones
                  </Typography>
                  {progressInfo.currentChunk > 0 && (
                    <Typography variant="caption" color="primary" sx={{ fontWeight: 'medium' }}>
                      Sección {progressInfo.currentChunk} de {progressInfo.totalChunks}
                    </Typography>
                  )}
                </Box>
              )}
              
              {/* Mensaje de estado al finalizar */}
              {progressInfo.percentage >= 100 && (
                <Box sx={{ mt: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="caption" color="success.main" sx={{ fontWeight: 'medium' }}>
                    ✓ Análisis completado exitosamente
                  </Typography>
                </Box>
              )}
            </Box>
          )}

          {/* Botón de análisis */}
          <Button
            variant="contained"
            color="primary"
            size="large"
            type="submit"
            disabled={loading || selectedFiles.length === 0}
            startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
            sx={{ mt: 3 }}
            fullWidth
          >
            {loading ? 'Analizando base de datos...' : `Analizar proyecto de BD (${selectedFiles.length} archivos)`}
          </Button>
        </Box>
      </Paper>

      {/* Mensaje de error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Mensaje informativo */}
      {!selectedFiles.length && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>¿Cómo funciona?</strong>
          </Typography>
          <Typography variant="body2">
            1. Haz clic en "Seleccionar Carpeta SQL" y elige la carpeta raíz de tu proyecto de base de datos
          </Typography>
          <Typography variant="body2">
            2. El sistema automáticamente creará un ZIP preservando la estructura
          </Typography>
          <Typography variant="body2">
            3. Se analizarán todos los archivos .sql, .ddl, .proc, .mysql, .pgsql y otros archivos de BD
          </Typography>
          <Typography variant="body2">
            4. Se aplicará consolidación automática si el proyecto es muy grande
          </Typography>
        </Alert>
      )}

      {/* Sección de resultados */}
      {loading ? (
        <Box sx={styles.loadingContainer}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Analizando estructura de la base de datos y generando documentación...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Este proceso puede tomar algunos minutos dependiendo del tamaño del proyecto de base de datos
          </Typography>
        </Box>
      ) : (directoryTree || userStories || defAnalysis) && (
        <Box>
          {/* Resumen del análisis */}
          {summary && (
            <AnalysisSummary summary={summary} timestamp={timestamp} />
          )}

          <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
            {/* Panel izquierdo: Estadísticas y estructura */}
            <Box sx={{ width: { xs: '100%', md: '35%' } }}>
              {directoryTree && (
                <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center' }}>
                    <StorageIcon sx={{ mr: 1 }} /> Estructura del Proyecto
                  </Typography>
                  <TreeView data={directoryTree} />
                </Paper>
              )}
              
              {projectStats && (
                <ProjectStats stats={projectStats} codeAnalysis={codeAnalysis} />
              )}
            </Box>
            
            {/* Panel derecho: Análisis */}
            {(userStories || defAnalysis) && (
              <Box sx={{ width: { xs: '100%', md: '65%' } }}>
                <Paper elevation={3} sx={{ p: 3 }}>
                  {/* Pestañas para cambiar entre historias de usuario y análisis DEF */}
                  <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs value={tabValue} onChange={handleTabChange} aria-label="analysis tabs">
                      <Tab 
                        label={
                          <Badge badgeContent={userStories ? "✓" : "0"} color="success">
                            Épicas e Historias de Usuario
                          </Badge>
                        } 
                        icon={<AssignmentIcon />}
                        iconPosition="start"
                      />
                      <Tab 
                        label={
                          <Badge badgeContent={defAnalysis ? "✓" : "0"} color="success">
                            Análisis DEF
                          </Badge>
                        } 
                        icon={<DescriptionIcon />}
                        iconPosition="start"
                      />
                    </Tabs>
                  </Box>

                  {/* Panel de Épicas e Historias de Usuario */}
                  <TabPanel value={tabValue} index={0}>
                    {userStories && (
                      <ContentViewer
                        content={userStories}
                        title="Épicas e Historias de Usuario Generadas"
                        filename={`epicas-historias-usuario-${projectName || 'proyecto'}.md`}
                        viewMode={viewMode}
                        setViewMode={setViewMode}
                      />
                    )}
                  </TabPanel>

                  {/* Panel de Análisis DEF */}
                  <TabPanel value={tabValue} index={1}>
                    {defAnalysis && (
                      <ContentViewer
                        content={defAnalysis}
                        title="Análisis para DEF (Definición de Requerimientos Funcionales)"
                        filename={`analisis-def-bd-${projectName || 'proyecto'}.md`}
                        viewMode={viewMode}
                        setViewMode={setViewMode}
                      />
                    )}
                  </TabPanel>
                </Paper>
              </Box>
            )}
          </Box>
        </Box>
      )}
    </Container>
  );
};

export default AnalizarCodigoSQL;