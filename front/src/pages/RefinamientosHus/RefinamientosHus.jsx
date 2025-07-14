import React, { useState, useRef } from 'react';
import { 
  Box, Button, Typography, Paper, CircularProgress, Divider,
  Tabs, Tab, Grid, List, ListItem, ListItemIcon, ListItemText,
  Card, CardContent, Chip, 
  Snackbar, Alert
} from '@mui/material';
import { 
  Upload as UploadIcon, 
  PictureAsPdf as PdfIcon,
  Check as CheckIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Lightbulb as LightbulbIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import Editor from '@monaco-editor/react';

const RefinamientosHus = () => {
  // Estados para el manejo de archivos
  const [files, setFiles] = useState([]);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  
  // Estados para resultados de análisis
  const [analysis, setAnalysis] = useState(null);
  const [currentTab, setCurrentTab] = useState(0);
  
  // Estados para edición y visualización de código
  const [currentFileIndex, setCurrentFileIndex] = useState(0);
  const [editorLanguage, setEditorLanguage] = useState('javascript');
  
  // Estado para notificaciones
  const [notification, setNotification] = useState({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // Referencias
  const fileInputRef = useRef(null);
  const editorRef = useRef(null);
  
  // Manejo de archivos
  const handleFileChange = (event) => {
    const selectedFiles = Array.from(event.target.files);
    const pdfFiles = selectedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== selectedFiles.length) {
      showNotification('Solo se permiten archivos PDF', 'warning');
    }
    
    setFiles(pdfFiles);
  };
  
  const handleDrop = (event) => {
    event.preventDefault();
    event.stopPropagation();
    
    const droppedFiles = Array.from(event.dataTransfer.files);
    const pdfFiles = droppedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== droppedFiles.length) {
      showNotification('Solo se permiten archivos PDF', 'warning');
    }
    
    setFiles(pdfFiles);
  };
  
  const handleDragOver = (event) => {
    event.preventDefault();
    event.stopPropagation();
  };
  
  // Función para analizar las historias de usuario
  const analyzeUserStories = async () => {
    if (files.length === 0) {
      showNotification('Por favor, selecciona al menos un archivo PDF', 'warning');
      return;
    }
    
    setIsAnalyzing(true);
    
    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await fetch('http://127.0.0.1:5000/api/analyze-user-stories', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        throw new Error(`Error en la solicitud: ${response.statusText}`);
      }
      
      const result = await response.json();
      setAnalysis(result);
      
      // Configurar el primer archivo para el editor
      if (result.generatedFiles && result.generatedFiles.length > 0) {
        setCurrentFileIndex(0);
        setEditorLanguage(getEditorLanguage(result.generatedFiles[0].name));
      }
      
      showNotification('Análisis completado con éxito', 'success');
    } catch (error) {
      console.error('Error al analizar los archivos:', error);
      showNotification(`Error: ${error.message}`, 'error');
    } finally {
      setIsAnalyzing(false);
    }
  };
  
  // Función para obtener el lenguaje del editor basado en la extensión del archivo
  const getEditorLanguage = (filename) => {
    const extension = filename.split('.').pop().toLowerCase();
    const languageMap = {
      'js': 'javascript',
      'jsx': 'javascript',
      'ts': 'typescript',
      'tsx': 'typescript',
      'py': 'python',
      'java': 'java',
      'cs': 'csharp',
      'go': 'go',
      'html': 'html',
      'css': 'css',
      'json': 'json',
      'md': 'markdown',
      'sql': 'sql',
      'yml': 'yaml',
      'yaml': 'yaml',
      'xml': 'xml',
      'php': 'php',
      'rb': 'ruby'
    };
    
    return languageMap[extension] || 'plaintext';
  };
  
  // Manejo de pestañas
  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
  };
  
  const handleFileTabChange = (index) => {
    setCurrentFileIndex(index);
    if (analysis?.generatedFiles?.[index]) {
      setEditorLanguage(getEditorLanguage(analysis.generatedFiles[index].name));
    }
  };
  
  // Notificaciones
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
  
  // Manejo del editor
  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
  };
  
  // Renderizar el icono según la severidad
  const renderSeverityIcon = (severity) => {
    switch (severity) {
      case 'high':
        return <ErrorIcon color="error" />;
      case 'medium':
        return <WarningIcon color="warning" />;
      case 'low':
        return <CheckIcon color="success" />;
      default:
        return <LightbulbIcon color="info" />;
    }
  };
  
  // Renderizar el color del chip según la categoría
  const getCategoryColor = (category) => {
    switch (category) {
      case 'functional':
        return 'primary';
      case 'technical':
        return 'secondary';
      case 'non-functional':
        return 'success';
      case 'missing':
        return 'warning';
      default:
        return 'default';
    }
  };
  
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Cabecera */}
      <Paper elevation={2} sx={{ p: 2, mb: 2, borderRadius: 0 }}>
        <Typography variant="h5" component="h1" gutterBottom>
          Analizador de Historias de Usuario
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Carga archivos PDF con historias de usuario para analizarlas y recibir recomendaciones técnicas, funcionales y no funcionales.
        </Typography>
      </Paper>
      
      {/* Contenido principal */}
      <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
        {/* Panel izquierdo: Carga de archivos y análisis general */}
        <Box sx={{ width: 300, p: 2, borderRight: 1, borderColor: 'divider', overflow: 'auto' }}>
          {/* Sección para cargar archivos */}
          <Paper
            elevation={0}
            sx={{
              p: 2,
              mb: 2,
              border: '2px dashed #ccc',
              textAlign: 'center',
              cursor: 'pointer',
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
              accept=".pdf"
            />
            <UploadIcon sx={{ fontSize: 40, color: 'text.secondary', mb: 1 }} />
            <Typography variant="body1" gutterBottom>
              Arrastra archivos PDF aquí
            </Typography>
            <Typography variant="body2" color="text.secondary">
              o haz clic para seleccionar
            </Typography>
          </Paper>
          
          {/* Lista de archivos cargados */}
          {files.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle1" gutterBottom>
                Archivos seleccionados ({files.length})
              </Typography>
              <List dense>
                {files.map((file, index) => (
                  <ListItem key={index}>
                    <ListItemIcon>
                      <PdfIcon color="error" />
                    </ListItemIcon>
                    <ListItemText 
                      primary={file.name} 
                      secondary={`${(file.size / 1024).toFixed(2)} KB`} 
                    />
                  </ListItem>
                ))}
              </List>
              <Button
                variant="contained"
                color="primary"
                fullWidth
                onClick={analyzeUserStories}
                disabled={isAnalyzing}
                startIcon={isAnalyzing ? <CircularProgress size={20} color="inherit" /> : <CodeIcon />}
                sx={{ mt: 2 }}
              >
                {isAnalyzing ? 'Analizando...' : 'Analizar Historias'}
              </Button>
            </Box>
          )}
          
          {/* Resumen del análisis */}
          {analysis && (
            <Box>
              <Typography variant="subtitle1" gutterBottom>
                Resumen del análisis
              </Typography>
              <Card variant="outlined" sx={{ mb: 2 }}>
                <CardContent>
                  <Typography variant="body2" gutterBottom>
                    <strong>Archivos analizados:</strong> {analysis.filesAnalyzed}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Historias encontradas:</strong> {analysis.totalUserStories}
                  </Typography>
                  <Typography variant="body2" gutterBottom>
                    <strong>Recomendaciones:</strong> {analysis.totalRecommendations}
                  </Typography>
                  <Typography variant="body2">
                    <strong>Información faltante:</strong> {analysis.missingInformation.length}
                  </Typography>
                </CardContent>
              </Card>
            </Box>
          )}
        </Box>
        
        {/* Panel principal: Resultados del análisis */}
        <Box sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {!analysis ? (
            // Mensaje cuando no hay análisis
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
              <Typography variant="body1" color="text.secondary">
                Carga archivos PDF y haz clic en "Analizar Historias" para comenzar
              </Typography>
            </Box>
          ) : (
            // Resultados del análisis
            <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
                <Tabs 
                  value={currentTab} 
                  onChange={handleTabChange} 
                  variant="scrollable"
                  scrollButtons="auto"
                >
                  <Tab label="Recomendaciones" />
                  <Tab label="Información Faltante" />
                  <Tab label="Archivos Generados" />
                  <Tab label="Análisis por Historia" />
                </Tabs>
              </Box>
              
              {/* Pestaña de Recomendaciones */}
              {currentTab === 0 && (
                <Box sx={{ p: 2, overflow: 'auto' }}>
                  <Grid container spacing={2}>
                    {analysis.recommendations.map((recommendation, index) => (
                      <Grid item xs={12} md={6} key={index}>
                        <Card variant="outlined">
                          <CardContent>
                            <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                              {renderSeverityIcon(recommendation.severity)}
                              <Typography variant="subtitle1" sx={{ ml: 1 }}>
                                {recommendation.title}
                              </Typography>
                            </Box>
                            <Typography variant="body2" gutterBottom>
                              {recommendation.description}
                            </Typography>
                            <Box sx={{ mt: 2 }}>
                              <Chip 
                                label={recommendation.category} 
                                size="small" 
                                color={getCategoryColor(recommendation.category)}
                                sx={{ mr: 1 }}
                              />
                              {recommendation.tags.map((tag, tagIndex) => (
                                <Chip 
                                  key={tagIndex} 
                                  label={tag} 
                                  size="small" 
                                  variant="outlined"
                                  sx={{ mr: 1 }}
                                />
                              ))}
                            </Box>
                          </CardContent>
                        </Card>
                      </Grid>
                    ))}
                  </Grid>
                </Box>
              )}
              
              {/* Pestaña de Información Faltante */}
              {currentTab === 1 && (
                <Box sx={{ p: 2, overflow: 'auto' }}>
                  <List>
                    {analysis.missingInformation.map((item, index) => (
                      <ListItem key={index} divider sx={{ py: 2 }}>
                        <ListItemIcon>
                          <WarningIcon color="warning" />
                        </ListItemIcon>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center' }}>
                              <Typography variant="subtitle1">
                                {item.story}
                              </Typography>
                              <Chip 
                                label={item.type} 
                                size="small" 
                                color="warning" 
                                variant="outlined"
                                sx={{ ml: 1 }}
                              />
                            </Box>
                          }
                          secondary={
                            <Typography variant="body2" sx={{ mt: 1 }}>
                              {item.description}
                            </Typography>
                          }
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
              
              {/* Pestaña de Archivos Generados */}
              {currentTab === 2 && (
                <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
                  <Box sx={{ p: 1, borderBottom: 1, borderColor: 'divider', display: 'flex', flexWrap: 'wrap' }}>
                    {analysis.generatedFiles.map((file, index) => (
                      <Chip
                        key={index}
                        label={file.name}
                        onClick={() => handleFileTabChange(index)}
                        sx={{ 
                          m: 0.5, 
                          backgroundColor: currentFileIndex === index ? 'primary.main' : 'default',
                          color: currentFileIndex === index ? 'white' : 'inherit'
                        }}
                      />
                    ))}
                  </Box>
                  
                  <Box sx={{ flexGrow: 1, overflow: 'hidden' }}>
                    {analysis.generatedFiles.length > 0 && (
                      <Editor
                        height="100%"
                        language={editorLanguage}
                        value={analysis.generatedFiles[currentFileIndex].content}
                        onMount={handleEditorDidMount}
                        options={{
                          readOnly: true,
                          minimap: { enabled: true },
                          scrollBeyondLastLine: false,
                          fontSize: 14,
                          wordWrap: 'on'
                        }}
                        theme="vs-dark"
                      />
                    )}
                  </Box>
                </Box>
              )}
              
              {/* Pestaña de Análisis por Historia */}
              {currentTab === 3 && (
                <Box sx={{ p: 2, overflow: 'auto' }}>
                  {analysis.userStories.map((story, index) => (
                    <Card key={index} variant="outlined" sx={{ mb: 2 }}>
                      <CardContent>
                        <Typography variant="h6" gutterBottom>
                          {story.title}
                        </Typography>
                        
                        <Box sx={{ border: 1, borderColor: 'divider', p: 1, mb: 2, borderRadius: 1, bgcolor: 'grey.50' }}>
                          <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                            {story.content}
                          </Typography>
                        </Box>
                        
                        <Typography variant="subtitle2" gutterBottom>
                          Análisis:
                        </Typography>
                        
                        <Typography variant="body2" paragraph>
                          {story.analysis}
                        </Typography>
                        
                        <Divider sx={{ my: 1 }} />
                        
                        <Typography variant="subtitle2" gutterBottom>
                          Problemas Detectados:
                        </Typography>
                        
                        <List dense>
                          {story.issues.map((issue, issueIndex) => (
                            <ListItem key={issueIndex}>
                              <ListItemIcon>
                                {renderSeverityIcon(issue.severity)}
                              </ListItemIcon>
                              <ListItemText 
                                primary={issue.title} 
                                secondary={issue.description} 
                              />
                            </ListItem>
                          ))}
                        </List>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </Box>
          )}
        </Box>
      </Box>
      
      {/* Notificación */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
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

export default RefinamientosHus;