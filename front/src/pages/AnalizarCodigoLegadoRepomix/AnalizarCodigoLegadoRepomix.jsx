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
  ContentCopy as ContentCopyIcon,
  Memory as MemoryIcon,
  Build as BuildIcon,
  Sync as SyncIcon,
  Engineering as EngineeringIcon,
  Psychology as PsychologyIcon
} from '@mui/icons-material';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import axios from 'axios';
import io from 'socket.io-client';

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
  },
  progressCard: {
    mb: 3,
    p: 2,
    border: '2px solid',
    borderColor: 'primary.main',
    borderRadius: 2
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

// Componente para mostrar progreso del análisis en tiempo real
const AnalysisProgress = ({ progressData, isVisible }) => {
  if (!isVisible || !progressData) return null;

  return (
    <Paper elevation={3} sx={styles.progressCard}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <SyncIcon sx={{ mr: 1, color: 'primary.main' }} />
        <Typography variant="h6" color="primary">
          Análisis en Progreso
        </Typography>
      </Box>
      
      <Typography variant="body2" gutterBottom>
        {progressData.phase}
      </Typography>
      
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
        <Box sx={{ width: '100%', mr: 1 }}>
          <LinearProgress 
            variant="determinate" 
            value={progressData.progress || 0} 
            sx={{ height: 8, borderRadius: 5 }}
          />
        </Box>
        <Box sx={{ minWidth: 35 }}>
          <Typography variant="body2" color="text.secondary">
            {`${Math.round(progressData.progress || 0)}%`}
          </Typography>
        </Box>
      </Box>
      
      {progressData.total_chunks > 1 && (
        <Typography variant="caption" color="text.secondary">
          Procesando chunk {progressData.current_chunk || 0} de {progressData.total_chunks}
        </Typography>
      )}
      
      <Typography variant="caption" display="block" color="text.secondary" sx={{ mt: 1 }}>
        Session ID: {progressData.session_id}
      </Typography>
    </Paper>
  );
};

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
          <AssessmentIcon sx={{ mr: 1 }} /> Estadísticas del Proyecto C/C++
        </Typography>
        
        <TableContainer>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell component="th" scope="row">Lenguaje:</TableCell>
                <TableCell align="right">
                  <Chip label={codeAnalysis?.language || 'C/C++ Legacy'} color="primary" size="small" />
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
                <TableCell component="th" scope="row">Archivos C:</TableCell>
                <TableCell align="right">{stats.c_files || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos C++:</TableCell>
                <TableCell align="right">{stats.cpp_files || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos de cabecera:</TableCell>
                <TableCell align="right">{stats.header_files || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Funciones encontradas:</TableCell>
                <TableCell align="right">{stats.total_functions || codeAnalysis?.total_functions || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Clases encontradas:</TableCell>
                <TableCell align="right">{stats.total_classes || codeAnalysis?.total_classes || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Estructuras encontradas:</TableCell>
                <TableCell align="right">{stats.total_structs || codeAnalysis?.total_structs || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Includes encontrados:</TableCell>
                <TableCell align="right">{stats.total_includes || codeAnalysis?.total_includes || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Defines encontrados:</TableCell>
                <TableCell align="right">{stats.total_defines || codeAnalysis?.total_defines || 0}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">APIs encontradas:</TableCell>
                <TableCell align="right">{stats.total_apis || codeAnalysis?.total_apis || 0}</TableCell>
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

        {codeAnalysis?.compilers_detected && codeAnalysis.compilers_detected.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Compiladores detectados:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {codeAnalysis.compilers_detected.map((compiler, index) => (
                <Chip
                  key={index}
                  label={compiler}
                  size="small"
                  color="secondary"
                  variant="outlined"
                  sx={{ mb: 1 }}
                />
              ))}
            </Stack>
          </Box>
        )}

        {codeAnalysis?.frameworks_found && codeAnalysis.frameworks_found.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Frameworks encontrados:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {codeAnalysis.frameworks_found.map((framework, index) => (
                <Chip
                  key={index}
                  label={framework}
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
            Análisis de código legado completado exitosamente
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
          {summary?.optimization_applied && (
            <Typography variant="body2" color="success.main">
              ✓ Optimización aplicada
            </Typography>
          )}
          {summary?.document_types_generated && (
            <Typography variant="body2" color="success.main">
              ✓ Documentos generados: {summary.document_types_generated.join(', ')}
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

const AnalizarCodigoLegadoRepomix = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [projectName, setProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  
  // CAMBIO PRINCIPAL - Estados actualizados para recibir DEF y DAT del backend
  const [defAnalysis, setDefAnalysis] = useState(''); // DEF - Especificación Funcional (antes userStories)
  const [datAnalysis, setDatAnalysis] = useState(''); // DAT - Análisis Técnico (antes defAnalysis)
  
  const [analyzedFiles, setAnalyzedFiles] = useState([]);
  const [directoryTree, setDirectoryTree] = useState(null);
  const [projectStats, setProjectStats] = useState(null);
  const [codeAnalysis, setCodeAnalysis] = useState(null);
  const [summary, setSummary] = useState(null);
  const [timestamp, setTimestamp] = useState('');
  const [tabValue, setTabValue] = useState(0);
  const [folderStructure, setFolderStructure] = useState(null);
  const [viewMode, setViewMode] = useState(0); // 0: rendered, 1: raw
  
  // Estados para WebSocket y progreso en tiempo real
  const [socket, setSocket] = useState(null);
  const [analysisProgress, setAnalysisProgress] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);

  // Extensiones permitidas para código legado C/C++ - ACTUALIZADO para coincidir con el backend
  const allowedExtensions = ['.c', '.cpp', '.cxx', '.cc', '.c++', '.h', '.hpp', '.hxx', '.hh', 
                            '.h++', '.inc', '.inl', '.ipp', '.txx', '.tcc', '.def', '.rc', 
                            '.res', '.asm', '.s', '.S', '.lib', '.dll', '.obj', '.o', 
                            '.make', '.mk', '.cmake', '.pro', '.vcproj', '.vcxproj', 
                            '.sln', '.dsp', '.dsw', '.cbp', '.dev'];

  // Configurar WebSocket cuando el componente se monta
  useEffect(() => {
    const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';
    const newSocket = io(API_BASE_URL);
    
    newSocket.on('connect', () => {
      console.log('WebSocket conectado');
    });

    newSocket.on('analysis_progress', (data) => {
      console.log('Progreso recibido:', data);
      if (sessionId && data.session_id === sessionId) {
        setAnalysisProgress(data);
      }
    });

    newSocket.on('analysis_complete', (data) => {
      console.log('Análisis completado:', data);
      if (sessionId && data.session_id === sessionId) {
        setIsAnalyzing(false);
        setAnalysisProgress(null);
      }
    });

    newSocket.on('analysis_error', (data) => {
      console.log('Error en análisis:', data);
      if (sessionId && data.session_id === sessionId) {
        setIsAnalyzing(false);
        setError(data.error);
        setAnalysisProgress(null);
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
           ['CMakeLists.txt', 'Makefile', 'makefile', 'configure', 'README.md', 'LICENSE'].includes(filename);
  };

  // Función para construir estructura de carpetas a partir de archivos
  const buildFolderStructure = (files) => {
    const structure = { name: projectName || 'Proyecto de Código Legado', type: 'folder', children: [], files: [] };
    
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
      setError('No se encontraron archivos de código C/C++ en la carpeta seleccionada');
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
      setError('Por favor, selecciona una carpeta con código C/C++');
      return;
    }

    if (!projectName.trim()) {
      setError('Por favor, ingresa un nombre para el proyecto');
      return;
    }

    // Generar session ID único
    const newSessionId = `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(newSessionId);
    
    setLoading(true);
    setIsAnalyzing(true);
    setError(null);
    setUploadProgress(10);
    setAnalysisProgress({ 
      session_id: newSessionId, 
      progress: 0, 
      phase: 'Iniciando análisis...', 
      current_chunk: 0, 
      total_chunks: 1 
    });

    try {
      // Crear ZIP automáticamente
      setUploadProgress(30);
      const zipBlob = await createZipFromFiles(selectedFiles);
      
      setUploadProgress(50);
      
      const formData = new FormData();
      formData.append('zip_file', zipBlob, `${projectName}.zip`);
      formData.append('project_name', projectName.trim());
      
      // ENDPOINT CORREGIDO - usar la ruta del backend
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';

      const response = await axios.post(`${API_BASE_URL}/api/analizarCodigoRepomix/zip`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = 50 + Math.round((progressEvent.loaded * 40) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      setUploadProgress(100);

      // CAMBIO CRÍTICO - Actualizar para usar las nuevas propiedades del backend
      setDefAnalysis(response.data.def_analysis || ''); // DEF - Especificación Funcional 
      setDatAnalysis(response.data.dat_analysis || ''); // DAT - Análisis Técnico
      
      setAnalyzedFiles(response.data.analyzed_files || []);
      setDirectoryTree(response.data.directory_tree || folderStructure);
      setProjectStats(response.data.project_stats || null);
      setCodeAnalysis(response.data.code_analysis || null);
      setSummary(response.data.summary || null);
      setTimestamp(response.data.timestamp || '');
      
    } catch (err) {
      console.error("Error completo:", err);
      setError(err.response?.data?.error || err.message || 'Ocurrió un error al analizar el código legado');
      setIsAnalyzing(false);
      setAnalysisProgress(null);
    } finally {
      setLoading(false);
      setUploadProgress(0);
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
    setAnalysisProgress(null);
    setSessionId(null);
    setIsAnalyzing(false);
  };

  return (
    <Container maxWidth="lg" sx={styles.container}>
      {/* Cabecera ACTUALIZADA */}
      <Box sx={styles.header}>
        <MemoryIcon sx={styles.headerIcon} />
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Análisis de Código Legado C/C++ - DEF + DAT
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Selecciona una carpeta con código legado C/C++ y genera DEF (Especificación Funcional) y DAT (Análisis Técnico) utilizando IA
          </Typography>
        </Box>
      </Box>

      {/* Progreso del análisis en tiempo real */}
      <AnalysisProgress 
        progressData={analysisProgress} 
        isVisible={isAnalyzing || loading} 
      />

      {/* Sección de entrada */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Seleccionar carpeta con código legado C/C++
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit} sx={styles.inputSection}>
          {/* Nombre del proyecto */}
          <TextField
            fullWidth
            label="Nombre del proyecto de código legado"
            variant="outlined"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Mi Proyecto Legacy C++"
            sx={{ mb: 3 }}
            required
            disabled={loading}
          />

          {/* Selector de carpeta */}
          <Box sx={styles.folderSelector}>
            <MemoryIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Seleccionar carpeta con código legado C/C++
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Haz clic para seleccionar una carpeta que contenga código legado C/C++, DLLs, bibliotecas, etc.
            </Typography>
            
            <Button
              variant="outlined"
              component="label"
              startIcon={<FolderOpenIcon />}
              size="large"
              disabled={loading}
            >
              Seleccionar Carpeta de Código Legacy
              <input
                type="file"
                hidden
                webkitdirectory=""
                directory=""
                multiple
                onChange={handleFolderSelect}
                disabled={loading}
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
                  disabled={loading}
                >
                  Limpiar
                </Button>
              </Box>
              <TreeView data={folderStructure} />
            </Paper>
          )}

          {/* Progreso de procesamiento */}
          {loading && uploadProgress > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>
                {uploadProgress < 30 ? 'Preparando archivos...' :
                 uploadProgress < 50 ? 'Creando archivo ZIP...' :
                 uploadProgress < 90 ? 'Subiendo y analizando...' : 'Finalizando análisis...'}
                {' '}{uploadProgress}%
              </Typography>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
          )}

          {/* Botón de análisis ACTUALIZADO */}
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
            {loading ? 'Generando DEF + DAT...' : `Analizar proyecto legacy (${selectedFiles.length} archivos)`}
          </Button>
        </Box>
      </Paper>

      {/* Mensaje de error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Mensaje informativo ACTUALIZADO */}
      {!selectedFiles.length && (
        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2">
            <strong>¿Cómo funciona?</strong>
          </Typography>
          <Typography variant="body2">
            1. Haz clic en "Seleccionar Carpeta de Código Legacy" y elige la carpeta raíz de tu proyecto C/C++
          </Typography>
          <Typography variant="body2">
            2. El sistema automáticamente creará un ZIP preservando la estructura
          </Typography>
          <Typography variant="body2">
            3. Se analizarán todos los archivos .c, .cpp, .h, .hpp, DLLs, y archivos de configuración
          </Typography>
          <Typography variant="body2">
            4. Se aplicará consolidación automática si el proyecto es muy grande
          </Typography>
          <Typography variant="body2">
            5. Se generarán 2 documentos: <strong>DEF (Especificación Funcional)</strong> y <strong>DAT (Análisis Técnico)</strong>
          </Typography>
          <Typography variant="body2">
            6. Podrás ver el progreso del análisis en tiempo real con WebSockets
          </Typography>
        </Alert>
      )}

      {/* Sección de resultados ACTUALIZADA */}
      {loading ? (
        <Box sx={styles.loadingContainer}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Analizando estructura del código legado y generando DEF + DAT...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Generando DEF (Especificación Funcional) y DAT (Análisis Técnico)
          </Typography>
          {sessionId && (
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
              Session ID: {sessionId}
            </Typography>
          )}
        </Box>
      ) : (directoryTree || defAnalysis || datAnalysis) && (
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
                    <StorageIcon sx={{ mr: 1 }} /> Estructura del Proyecto Legacy
                  </Typography>
                  <TreeView data={directoryTree} />
                </Paper>
              )}
              
              {projectStats && (
                <ProjectStats stats={projectStats} codeAnalysis={codeAnalysis} />
              )}
            </Box>
            
            {/* Panel derecho: Análisis ACTUALIZADO */}
            {(defAnalysis || datAnalysis) && (
              <Box sx={{ width: { xs: '100%', md: '65%' } }}>
                <Paper elevation={3} sx={{ p: 3 }}>
                  {/* Pestañas ACTUALIZADAS con nuevos nombres y iconos */}
                  <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                    <Tabs value={tabValue} onChange={handleTabChange} aria-label="analysis tabs">
                      <Tab 
                        label={
                          <Badge badgeContent={defAnalysis ? "✓" : "0"} color="success">
                            DEF - Especificación Funcional
                          </Badge>
                        } 
                        icon={<PsychologyIcon />}
                        iconPosition="start"
                      />
                      <Tab 
                        label={
                          <Badge badgeContent={datAnalysis ? "✓" : "0"} color="success">
                            DAT - Análisis Técnico
                          </Badge>
                        } 
                        icon={<EngineeringIcon />}
                        iconPosition="start"
                      />
                    </Tabs>
                  </Box>

                  {/* Panel de DEF Funcional ACTUALIZADO */}
                  <TabPanel value={tabValue} index={0} >
                    {defAnalysis && (
                      <ContentViewer
                        content={defAnalysis}
                        title="DEF - Documento de Especificación Funcional"
                        filename={`DEF-especificacion-funcional-${projectName || 'proyecto'}.md`}
                        viewMode={viewMode}
                        setViewMode={setViewMode}
                      />
                    )}
                  </TabPanel>

                  {/* Panel de DAT Técnico ACTUALIZADO */}
                  <TabPanel value={tabValue} index={1}>
                    {datAnalysis && (
                      <ContentViewer
                        content={datAnalysis}
                        title="DAT - Documento de Análisis Técnico"
                        filename={`DAT-analisis-tecnico-${projectName || 'proyecto'}.md`}
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

export default AnalizarCodigoLegadoRepomix;