import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardMedia,
  CircularProgress,
  Container,
  Divider,
  Grid,
  IconButton,
  Link,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Snackbar,
  Tab,
  Tabs,
  TextField,
  Typography,
  Alert,
  Chip,
  Stack
} from '@mui/material';

// Iconos
import SearchIcon from '@mui/icons-material/Search';
import ArticleIcon from '@mui/icons-material/Article';
import InsertLinkIcon from '@mui/icons-material/InsertLink';
import ImageIcon from '@mui/icons-material/Image';
import SummarizeIcon from '@mui/icons-material/Summarize';
import LaunchIcon from '@mui/icons-material/Launch';
import TagIcon from '@mui/icons-material/Tag';

function WebScraperApp() {
  // Estados
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [scrapedData, setScrapedData] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  // Manejar cambio de URL
  const handleUrlChange = (event) => {
    setUrl(event.target.value);
  };

  // Manejar cambio de pestaña
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  // Cerrar snackbar
  const handleCloseSnackbar = () => {
    setSnackbarOpen(false);
  };

  // Realizar scraping
  const handleScrape = async () => {
    // Validar URL
    if (!url) {
      setError('Por favor, introduce una URL');
      setSnackbarOpen(true);
      return;
    }

    try {
      // Validar formato URL
      new URL(url);
      
      setLoading(true);
      setError(null);
      
      // Llamar a la API
      const response = await fetch('http://localhost:5000/api/scrape', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Error al realizar el scraping');
      }

      const data = await response.json();
      setScrapedData(data);
      
    } catch (err) {
      if (err.name === 'TypeError' && err.message.includes('URL')) {
        setError('URL inválida. Asegúrate de incluir http:// o https://');
      } else {
        setError(err.message || 'Error al realizar el scraping');
      }
      setSnackbarOpen(true);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      {/* Título */}
      <Typography 
        variant="h4" 
        component="h1" 
        gutterBottom 
        align="center"
        sx={{ 
          mb: 4, 
          fontWeight: 'bold',
          color: 'primary.main' 
        }}
      >
        Web Scraper
      </Typography>
      
      {/* Formulario de búsqueda */}
      <Paper 
        elevation={3} 
        sx={{ 
          p: 3, 
          mb: 4, 
          borderRadius: 2,
          display: 'flex', 
          flexDirection: { xs: 'column', sm: 'row' },
          alignItems: 'center',
          gap: 2
        }}
      >
        <TextField
          label="URL de la página web"
          placeholder="https://ejemplo.com"
          variant="outlined"
          fullWidth
          value={url}
          onChange={handleUrlChange}
          disabled={loading}
          sx={{ flexGrow: 1 }}
        />
        <Button
          variant="contained"
          color="primary"
          size="large"
          startIcon={loading ? <CircularProgress size={24} color="inherit" /> : <SearchIcon />}
          onClick={handleScrape}
          disabled={loading}
          sx={{ 
            py: 1.5, 
            px: 4,
            minWidth: { xs: '100%', sm: 'auto' } 
          }}
        >
          {loading ? 'Analizando...' : 'Analizar'}
        </Button>
      </Paper>

      {/* Resultados del scraping */}
      {scrapedData && (
        <Card elevation={3} sx={{ borderRadius: 2 }}>
          <CardContent sx={{ p: 3 }}>
            {/* Título y URL */}
            <Typography variant="h5" gutterBottom>
              {scrapedData.title || 'Sin título'}
            </Typography>
            
            <Link 
              href={scrapedData.url} 
              target="_blank" 
              rel="noopener noreferrer"
              color="primary"
              sx={{ display: 'block', mb: 2 }}
            >
              {scrapedData.url}
            </Link>

            {/* Descripción */}
            {scrapedData.description && (
              <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 3 }}>
                {scrapedData.description}
              </Typography>
            )}

            {/* Palabras clave */}
            {scrapedData.keywords && scrapedData.keywords.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Palabras clave:
                </Typography>
                <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
                  {scrapedData.keywords.map((keyword, index) => (
                    <Chip 
                      key={index} 
                      label={keyword} 
                      size="small" 
                      icon={<TagIcon />}
                      variant="outlined"
                      color="primary"
                    />
                  ))}
                </Stack>
              </Box>
            )}

            <Divider sx={{ my: 3 }} />

            {/* Pestañas para diferentes tipos de contenido */}
            <Box>
              <Tabs 
                value={tabValue} 
                onChange={handleTabChange} 
                variant="scrollable"
                scrollButtons="auto"
                sx={{ mb: 2 }}
              >
                <Tab icon={<SummarizeIcon />} label="Resumen" />
                <Tab icon={<ArticleIcon />} label="Texto Completo" />
                <Tab icon={<InsertLinkIcon />} label="Enlaces" />
                <Tab icon={<ImageIcon />} label="Imágenes" />
              </Tabs>

              {/* Contenido de la pestaña: Resumen */}
              {tabValue === 0 && (
                <Box>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-line' }}>
                    {scrapedData.summary || 'No hay resumen disponible para esta página.'}
                  </Typography>
                </Box>
              )}

              {/* Contenido de la pestaña: Texto Completo */}
              {tabValue === 1 && (
                <Box sx={{ maxHeight: '400px', overflow: 'auto', p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line' }}>
                    {scrapedData.text || 'No se encontró texto en esta página.'}
                  </Typography>
                </Box>
              )}

              {/* Contenido de la pestaña: Enlaces */}
              {tabValue === 2 && (
                <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                  {scrapedData.links && scrapedData.links.length > 0 ? (
                    <List>
                      {scrapedData.links.map((link, index) => (
                        <ListItem 
                          key={index}
                          secondaryAction={
                            <IconButton 
                              edge="end" 
                              component="a"
                              href={link.url}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <LaunchIcon />
                            </IconButton>
                          }
                          sx={{ 
                            mb: 1,
                            border: '1px solid',
                            borderColor: 'divider',
                            borderRadius: 1,
                            bgcolor: link.internal ? 'rgba(25, 118, 210, 0.04)' : 'transparent'
                          }}
                        >
                          <ListItemIcon>
                            <InsertLinkIcon color={link.internal ? 'primary' : 'action'} />
                          </ListItemIcon>
                          <ListItemText
                            primary={link.text || 'Sin texto'}
                            secondary={link.url}
                            primaryTypographyProps={{ noWrap: true }}
                            secondaryTypographyProps={{ noWrap: true }}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No se encontraron enlaces en esta página.
                    </Typography>
                  )}
                </Box>
              )}

              {/* Contenido de la pestaña: Imágenes */}
              {tabValue === 3 && (
                <Box sx={{ maxHeight: '400px', overflow: 'auto' }}>
                  {scrapedData.images && scrapedData.images.length > 0 ? (
                    <Grid container spacing={2}>
                      {scrapedData.images.map((image, index) => (
                        <Grid item xs={12} sm={6} md={4} key={index}>
                          <Card elevation={1}>
                            <CardMedia
                              component="img"
                              height="160"
                              image={image.src || image}
                              alt={image.alt || `Imagen ${index + 1}`}
                              sx={{ objectFit: 'contain' }}
                              onError={(e) => {
                                e.target.onerror = null;
                                e.target.src = "https://via.placeholder.com/160x160?text=Imagen+no+disponible";
                              }}
                            />
                            <CardContent sx={{ py: 1 }}>
                              <Typography variant="caption" color="text.secondary" noWrap>
                                {image.alt || `Imagen ${index + 1}`}
                              </Typography>
                            </CardContent>
                          </Card>
                        </Grid>
                      ))}
                    </Grid>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No se encontraron imágenes en esta página.
                    </Typography>
                  )}
                </Box>
              )}
            </Box>
          </CardContent>
        </Card>
      )}

      {/* Snackbar para mensajes de error */}
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleCloseSnackbar} severity="error" variant="filled">
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
}

export default WebScraperApp;