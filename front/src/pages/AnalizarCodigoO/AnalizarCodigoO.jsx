import React, { useState } from 'react';
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
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
  LinearProgress
} from '@mui/material';
import {
  FolderOpen as FolderOpenIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  ExpandMore as ExpandMoreIcon,
  FileCopy as FileCopyIcon,
  InsertDriveFile as FileIcon,
  Folder as FolderIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowRight as KeyboardArrowRightIcon,
  Assessment as AssessmentIcon,
  Storage as StorageIcon,
  Assignment as AssignmentIcon,
  CloudDone as CloudDoneIcon,
  CheckCircle as CheckCircleIcon,
  Delete as DeleteIcon,
  Upload as UploadIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import axios from 'axios';

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
          <AssessmentIcon sx={{ mr: 1 }} /> Estadísticas del Proyecto
        </Typography>
        
        <TableContainer>
          <Table size="small">
            <TableBody>
              <TableRow>
                <TableCell component="th" scope="row">Lenguaje:</TableCell>
                <TableCell align="right">
                  <Chip label={codeAnalysis?.language || 'C/C++'} color="primary" size="small" />
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
                <TableCell component="th" scope="row">Archivos de cabecera:</TableCell>
                <TableCell align="right">{stats.header_files}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos fuente:</TableCell>
                <TableCell align="right">{stats.source_files}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Funciones encontradas:</TableCell>
                <TableCell align="right">{stats.total_functions}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Clases encontradas:</TableCell>
                <TableCell align="right">{stats.total_classes}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Estructuras encontradas:</TableCell>
                <TableCell align="right">{stats.total_structs}</TableCell>
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

        {codeAnalysis?.common_includes && codeAnalysis.common_includes.length > 0 && (
          <Box mt={2}>
            <Typography variant="subtitle2" gutterBottom>
              Includes más utilizados:
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap">
              {codeAnalysis.common_includes.map(([include, count], index) => (
                <Chip
                  key={index}
                  label={`${include} (${count})`}
                  size="small"
                  color="secondary"
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
            Análisis completado exitosamente
          </Typography>
          <Typography variant="body2">
            Método: Selección directa de carpeta
          </Typography>
          <Typography variant="body2">
            Análisis realizado el: {new Date().toLocaleString()}
          </Typography>
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

const AnalizarCodigoO = () => {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [projectName, setProjectName] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
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

  // Extensiones permitidas
  const allowedExtensions = ['.c', '.cpp', '.cc', '.cxx', '.c++', '.h', '.hpp', '.hxx', '.h++', 
                            '.rc', '.def', '.mk', '.mak', '.cmake', '.txt', '.md', '.json', '.xml'];

  // Función para verificar si un archivo es permitido
  const isAllowedFile = (filename) => {
    const ext = '.' + filename.split('.').pop().toLowerCase();
    return allowedExtensions.includes(ext) || 
           ['CMakeLists.txt', 'Makefile', 'makefile', 'configure'].includes(filename);
  };

  // Función para construir estructura de carpetas a partir de archivos
  const buildFolderStructure = (files) => {
    const structure = { name: projectName || 'Proyecto', type: 'folder', children: [], files: [] };
    
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

    setLoading(true);
    setError(null);
    setUploadProgress(10);

    try {
      // Crear ZIP automáticamente
      setUploadProgress(30);
      const zipBlob = await createZipFromFiles(selectedFiles);
      
      setUploadProgress(50);
      
      const formData = new FormData();
      formData.append('zip_file', zipBlob, `${projectName}.zip`);
      formData.append('project_name', projectName.trim());

      // CAMBIA ESTA URL POR LA DE TU SERVICIO EN LA NUBE
      const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://127.0.0.1:5000';

      const response = await axios.post(`${API_BASE_URL}/api/analizarCodigoo/zip`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const progress = 10 + Math.round((progressEvent.loaded * 40) / progressEvent.total);
          setUploadProgress(progress);
        }
      });

      setUploadProgress(100);

      // Establecer los resultados
      setUserStories(response.data.user_stories || '');
      setDefAnalysis(response.data.def_analysis || '');
      setAnalyzedFiles(response.data.analyzed_files || []);
      setDirectoryTree(response.data.directory_tree || folderStructure);
      setProjectStats(response.data.project_stats || null);
      setCodeAnalysis(response.data.code_analysis || null);
      setSummary(response.data.summary || null);
      setTimestamp(response.data.timestamp || '');
      
    } catch (err) {
      console.error("Error completo:", err);
      setError(err.response?.data?.error || err.message || 'Ocurrió un error al analizar el código');
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copiado al portapapeles');
  };

  // Función para descargar contenido como archivo Markdown
  const downloadAsMarkdown = (content, filename) => {
    const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    URL.revokeObjectURL(url);
  };

  // Función para formatear historias de usuario como Markdown
  const formatUserStoriesAsMarkdown = (stories) => {
    const projectNameFormatted = projectName || 'Proyecto';
    const dateFormatted = new Date().toLocaleDateString('es-ES');
    
    let markdown = `# Historias de Usuario - ${projectNameFormatted}\n\n`;
    markdown += `**Fecha de generación:** ${dateFormatted}\n\n`;
    markdown += `---\n\n`;
    
    const storiesArray = stories.split('Como').filter(story => story.trim());
    
    storiesArray.forEach((story, index) => {
      const fullStory = 'Como' + story.trim();
      const lines = fullStory.split('\n');
      const title = lines[0];
      
      markdown += `## Historia de Usuario ${index + 1}\n\n`;
      markdown += `**${title}**\n\n`;
      markdown += `${fullStory}\n\n`;
      markdown += `---\n\n`;
    });
    
    return markdown;
  };

  // Función para formatear análisis DEF como Markdown
  const formatDefAnalysisAsMarkdown = (analysis) => {
    const projectNameFormatted = projectName || 'Proyecto';
    const dateFormatted = new Date().toLocaleDateString('es-ES');
    
    let markdown = `# Análisis DEF - ${projectNameFormatted}\n\n`;
    markdown += `**Definición de Requerimientos Funcionales**\n\n`;
    markdown += `**Fecha de generación:** ${dateFormatted}\n\n`;
    markdown += `---\n\n`;
    markdown += analysis;
    
    return markdown;
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
            Análisis Código Legado C/C++ - Cloud
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Selecciona una carpeta de código y genera historias de usuario y análisis DEF utilizando IA
          </Typography>
        </Box>
      </Box>

      {/* Sección de entrada */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Seleccionar carpeta de código C/C++
        </Typography>
        
        <Box component="form" onSubmit={handleSubmit} sx={styles.inputSection}>
          {/* Nombre del proyecto */}
          <TextField
            fullWidth
            label="Nombre del proyecto"
            variant="outlined"
            value={projectName}
            onChange={(e) => setProjectName(e.target.value)}
            placeholder="Mi Proyecto C++"
            sx={{ mb: 3 }}
            required
          />

          {/* Selector de carpeta */}
          <Box sx={styles.folderSelector}>
            <FolderOpenIcon sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Seleccionar carpeta de código
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Haz clic para seleccionar una carpeta que contenga código C/C++
            </Typography>
            
            <Button
              variant="outlined"
              component="label"
              startIcon={<FolderOpenIcon />}
              size="large"
            >
              Seleccionar Carpeta
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
            {loading ? 'Analizando código...' : `Analizar proyecto (${selectedFiles.length} archivos)`}
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
            1. Haz clic en "Seleccionar Carpeta" y elige la carpeta raíz de tu proyecto C/C++
          </Typography>
          <Typography variant="body2">
            2. El sistema automáticamente creará un ZIP preservando la estructura
          </Typography>
          <Typography variant="body2">
            3. Se analizarán todos los archivos .c, .cpp, .h, .hpp y archivos de construcción
          </Typography>
        </Alert>
      )}

      {/* Sección de resultados */}
      {loading ? (
        <Box sx={styles.loadingContainer}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Analizando estructura del proyecto y generando documentación...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Este proceso puede tomar algunos minutos dependiendo del tamaño del proyecto
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
                            Historias de Usuario
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

                  {/* Panel de Historias de Usuario */}
                  <TabPanel value={tabValue} index={0}>
                    {userStories && (
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h5">
                            Historias de Usuario Generadas
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Copiar todo el texto">
                              <IconButton onClick={() => copyToClipboard(userStories)}>
                                <FileCopyIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Descargar como Markdown">
                              <IconButton 
                                onClick={() => downloadAsMarkdown(
                                  formatUserStoriesAsMarkdown(userStories),
                                  `historias-usuario-${projectName || 'proyecto'}.md`
                                )}
                              >
                                <DownloadIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                        
                        <Divider sx={{ my: 3 }} />
                        
                        {/* Historias de usuario */}
                        <Typography variant="h6" gutterBottom>
                          Historias de Usuario:
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, whiteSpace: 'pre-wrap' }}>
                          {userStories.split('Como').map((story, index) => {
                            if (index === 0) return null;
                            const fullStory = 'Como' + story;
                            return (
                              <Accordion key={index} sx={{ mb: 2 }}>
                                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <Chip label={`Historia ${index}`} color="primary" size="small" />
                                    <Typography variant="subtitle1">
                                      {fullStory.split('\n')[0]}
                                    </Typography>
                                  </Stack>
                                </AccordionSummary>
                                <AccordionDetails>
                                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                                    {fullStory}
                                  </Typography>
                                </AccordionDetails>
                              </Accordion>
                            );
                          })}
                        </Paper>
                      </Box>
                    )}
                  </TabPanel>

                  {/* Panel de Análisis DEF */}
                  <TabPanel value={tabValue} index={1}>
                    {defAnalysis && (
                      <Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h5">
                            Análisis para DEF (Definición de Requerimientos Funcionales)
                          </Typography>
                          <Box sx={{ display: 'flex', gap: 1 }}>
                            <Tooltip title="Copiar análisis completo">
                              <IconButton onClick={() => copyToClipboard(defAnalysis)}>
                                <FileCopyIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Descargar como Markdown">
                              <IconButton 
                                onClick={() => downloadAsMarkdown(
                                  formatDefAnalysisAsMarkdown(defAnalysis),
                                  `analisis-def-${projectName || 'proyecto'}.md`
                                )}
                              >
                                <DownloadIcon />
                              </IconButton>
                            </Tooltip>
                          </Box>
                        </Box>
                        
                        <Paper variant="outlined" sx={{ p: 3, whiteSpace: 'pre-wrap' }}>
                          <Typography variant="body1">
                            {defAnalysis}
                          </Typography>
                        </Paper>
                      </Box>
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

export default AnalizarCodigoO;