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
  TableRow
} from '@mui/material';
import {
  Folder as FolderIcon,
  Code as CodeIcon,
  Description as DescriptionIcon,
  ExpandMore as ExpandMoreIcon,
  FileCopy as FileCopyIcon,
  Save as SaveIcon,
  InsertDriveFile as FileIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
  KeyboardArrowRight as KeyboardArrowRightIcon,
  Assessment as AssessmentIcon,
  Storage as StorageIcon
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
  pathInput: {
    mb: 2
  },
  generateButton: {
    mt: 2
  },
  fileListContainer: {
    mt: 3,
    mb: 3
  },
  treeItem: {
    py: 0.5
  },
  nestedTreeItem: {
    pl: 4
  },
  outputFileSection: {
    mt: 3,
    mb: 3,
    p: 2,
    bgcolor: 'success.light',
    borderRadius: 1,
    display: 'flex',
    alignItems: 'center'
  },
  outputFileIcon: {
    mr: 2,
    color: 'success.dark'
  },
  userStoryCard: {
    mb: 2
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
  tokenUsageContainer: {
    mt: 2,
    pt: 2,
    borderTop: 1,
    borderColor: 'divider'
  },
  tokenCard: {
    p: 1,
    bgcolor: 'background.default',
    minWidth: '120px'
  }
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

  // Función recursiva para renderizar el árbol
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
            secondary={node.type === 'file' ? node.extension : null}
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
const ProjectStats = ({ stats }) => {
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
                <TableCell component="th" scope="row">Total de archivos:</TableCell>
                <TableCell align="right">{stats.total_files}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Archivos analizados:</TableCell>
                <TableCell align="right">{stats.analyzed_files}</TableCell>
              </TableRow>
              <TableRow>
                <TableCell component="th" scope="row">Total de líneas de código:</TableCell>
                <TableCell align="right">{stats.total_lines}</TableCell>
              </TableRow>
              {stats.largest_file && (
                <TableRow>
                  <TableCell component="th" scope="row">Archivo más grande:</TableCell>
                  <TableCell align="right">{stats.largest_file.name} ({(stats.largest_file.size / 1024).toFixed(2)} KB)</TableCell>
                </TableRow>
              )}
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
      </CardContent>
    </Card>
  );
};

// Componente para mostrar información de tokens
const TokenUsage = ({ tokenUsage }) => {
  return (
    <Box sx={styles.tokenUsageContainer}>
      <Typography variant="subtitle2" color="text.secondary" gutterBottom>
        Información de uso
      </Typography>
      <Box sx={{ display: 'flex', gap: 2, mt: 1, flexWrap: 'wrap' }}>
        <Tooltip title="Tokens usados en tu prompt">
          <Paper sx={styles.tokenCard}>
            <Typography variant="caption" color="text.secondary">
              Tokens del prompt
            </Typography>
            <Typography variant="h6">
              {tokenUsage.prompt_tokens.toLocaleString()}
            </Typography>
          </Paper>
        </Tooltip>
        
        <Tooltip title="Tokens generados en la respuesta">
          <Paper sx={styles.tokenCard}>
            <Typography variant="caption" color="text.secondary">
              Tokens de respuesta
            </Typography>
            <Typography variant="h6">
              {tokenUsage.completion_tokens.toLocaleString()}
            </Typography>
          </Paper>
        </Tooltip>
        
        <Tooltip title="Total de tokens utilizados">
          <Paper sx={styles.tokenCard}>
            <Typography variant="caption" color="text.secondary">
              Total de tokens
            </Typography>
            <Typography variant="h6" color="primary.main">
              {tokenUsage.total_tokens.toLocaleString()}
            </Typography>
          </Paper>
        </Tooltip>
      </Box>
    </Box>
  );
};

const Historias = () => {
  const [codePath, setCodePath] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [userStories, setUserStories] = useState('');
  const [analyzedFiles, setAnalyzedFiles] = useState([]);
  const [directoryTree, setDirectoryTree] = useState(null);
  const [projectStats, setProjectStats] = useState(null);
  const [outputFile, setOutputFile] = useState('');
  const [tokenUsage, setTokenUsage] = useState({
    prompt_tokens: 0,
    completion_tokens: 0,
    total_tokens: 0
  });

  // Función para normalizar rutas de Windows a formato con barras normales
  const normalizePath = (path) => {
    // Reemplazar todas las barras invertidas (\) por barras normales (/)
    let normalizedPath = path.replace(/\\/g, '/');
    
    // Asegurarse de que la letra de la unidad esté en mayúscula (para rutas Windows)
    if (/^[a-z]:/i.test(normalizedPath)) {
      normalizedPath = normalizedPath.charAt(0).toUpperCase() + normalizedPath.slice(1);
    }
    
    // Eliminar barras duplicadas si las hay
    normalizedPath = normalizedPath.replace(/\/+/g, '/');
    
    return normalizedPath;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!codePath) {
      setError('Por favor, ingresa la ruta del código');
      return;
    }

    // Asegurarse de que la ruta esté normalizada antes de enviarla
    const normalizedPath = normalizePath(codePath);

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post('http://127.0.0.1:5000/api/generate-user-stories', {
        code_path: normalizedPath
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });

      // Establecer los resultados
      setUserStories(response.data.user_stories);
      setAnalyzedFiles(response.data.analyzed_files || []);
      setDirectoryTree(response.data.directory_tree || null);
      setProjectStats(response.data.project_stats || null);
      setOutputFile(response.data.output_file || '');
      
      // Capturar información de tokens si existe
      if (response.data.token_usage) {
        setTokenUsage(response.data.token_usage);
      } else {
        // Si no hay información de tokens, reiniciar a 0
        setTokenUsage({
          prompt_tokens: 0,
          completion_tokens: 0,
          total_tokens: 0
        });
      }
    } catch (err) {
      console.error("Error completo:", err);
      setError(err.response?.data?.error || err.message || 'Ocurrió un error al generar las historias de usuario');
      
      // Si hay un árbol de directorios en la respuesta de error, mostrarlo
      if (err.response?.data?.directory_tree) {
        setDirectoryTree(err.response.data.directory_tree);
      }
      if (err.response?.data?.analyzed_files) {
        setAnalyzedFiles(err.response.data.analyzed_files);
      }
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    alert('Copiado al portapapeles');
  };

  return (
    <Container maxWidth="lg" sx={styles.container}>
      {/* Cabecera */}
      <Box sx={styles.header}>
        <CodeIcon sx={styles.headerIcon} />
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Generador de Historias de Usuario
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            Genera historias de usuario a partir de código legado utilizando IA
          </Typography>
        </Box>
      </Box>

      {/* Sección de entrada */}
      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Selecciona la ruta del código
        </Typography>
        <Box component="form" onSubmit={handleSubmit} sx={styles.inputSection}>
          <TextField
            fullWidth
            label="Ruta del código legado"
            variant="outlined"
            value={codePath}
            onChange={(e) => setCodePath(normalizePath(e.target.value))}
            placeholder="/ruta/a/tu/codigo"
            InputProps={{
              startAdornment: <FolderIcon color="action" sx={{ mr: 1 }} />,
            }}
            sx={styles.pathInput}
          />
          <Button
            variant="contained"
            color="primary"
            size="large"
            type="submit"
            disabled={loading}
            startIcon={loading ? <CircularProgress size={20} /> : <DescriptionIcon />}
            sx={styles.generateButton}
          >
            {loading ? 'Analizando código...' : 'Generar Historias de Usuario'}
          </Button>
        </Box>
      </Paper>

      {/* Mensaje de error */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Sección de resultados */}
      {loading ? (
        <Box sx={styles.loadingContainer}>
          <CircularProgress size={60} />
          <Typography variant="h6" sx={{ mt: 2 }}>
            Analizando código y generando historias de usuario...
          </Typography>
        </Box>
      ) : (directoryTree || userStories) && (
        <Box sx={{ display: 'flex', flexDirection: { xs: 'column', md: 'row' }, gap: 3 }}>
          {/* Panel izquierdo: Árbol de directorios y estadísticas */}
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
              <ProjectStats stats={projectStats} />
            )}
          </Box>
          
          {/* Panel derecho: Historias de usuario */}
          {userStories && (
            <Box sx={{ width: { xs: '100%', md: '65%' } }}>
              <Paper elevation={3} sx={{ p: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h5">
                    Historias de Usuario Generadas
                  </Typography>
                  <Tooltip title="Copiar todo el texto">
                    <IconButton onClick={() => copyToClipboard(userStories)}>
                      <FileCopyIcon />
                    </IconButton>
                  </Tooltip>
                </Box>
                
                {/* Archivos analizados */}
                <Box sx={styles.fileListContainer}>
                  <Typography variant="h6" gutterBottom>
                    Archivos Analizados:
                  </Typography>
                  <TableContainer component={Paper} variant="outlined">
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Nombre</TableCell>
                          <TableCell>Ruta</TableCell>
                          <TableCell align="right">Líneas</TableCell>
                          <TableCell align="right">Tamaño</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {analyzedFiles.map((file, index) => (
                          <TableRow key={index}>
                            <TableCell>{file.name}</TableCell>
                            <TableCell>{file.path}</TableCell>
                            <TableCell align="right">{file.lines}</TableCell>
                            <TableCell align="right">{(file.size / 1024).toFixed(2)} KB</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
                
                {/* Información de uso de tokens */}
                <TokenUsage tokenUsage={tokenUsage} />
                
                {/* Archivo de salida */}
                {outputFile && (
                  <Box sx={styles.outputFileSection}>
                    <SaveIcon sx={styles.outputFileIcon} />
                    <Box>
                      <Typography variant="subtitle1" fontWeight="bold">
                        Historias guardadas en:
                      </Typography>
                      <Typography variant="body2">
                        {outputFile}
                      </Typography>
                    </Box>
                  </Box>
                )}
                
                <Divider sx={{ my: 3 }} />
                
                {/* Historias de usuario */}
                <Typography variant="h6" gutterBottom>
                  Historias de Usuario:
                </Typography>
                <Paper variant="outlined" sx={{ p: 2, whiteSpace: 'pre-wrap' }}>
                  {userStories.split('Como').map((story, index) => {
                    if (index === 0) return null; // Saltar la primera parte que está vacía
                    const fullStory = 'Como' + story;
                    return (
                      <Accordion key={index} sx={styles.userStoryCard}>
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
              </Paper>
            </Box>
          )}
        </Box>
      )}
    </Container>
  );
};

export default Historias;