import React, { useState } from 'react';
import {
  Container,
  Typography,
  TextField,
  Button,
  Grid,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';

const Componente = () => {
  const [formData, setFormData] = useState({
    tipoDist: '',
    numPedido: '',
    tipoPedido: '',
    minimoDistri: '',
  });

  const [reportData, setReportData] = useState([]);

  // Manejo de cambios en los campos del formulario
  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData({ ...formData, [name]: value });
  };

  // Simulación de envío del formulario
  const handleSubmit = (event) => {
    event.preventDefault();

    // Simulación de lógica de negocio
    const generatedReport = [
      {
        numPedido: formData.numPedido || '12345',
        tipoPedido: formData.tipoPedido || 'N',
        numCodigo: '001',
        numTalla: 'M',
        cantidadPedida: 100,
        porcentaje: 95,
        ciudadDestino: 'CDMX',
        descMarca: 'Marca1',
        descFamilia: 'Ropa',
      },
    ];

    setReportData(generatedReport);
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" gutterBottom>
        Gestión de Distribución de Pedidos
      </Typography>

      {/* Formulario de distribución */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Distribuir Pedidos
        </Typography>
        <Box component="form" onSubmit={handleSubmit}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Tipo de Distribución"
                name="tipoDist"
                value={formData.tipoDist}
                onChange={handleChange}
                placeholder="1: Por Pedido, 2: Masivo"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Número de Pedido"
                name="numPedido"
                value={formData.numPedido}
                onChange={handleChange}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Tipo de Pedido"
                name="tipoPedido"
                value={formData.tipoPedido}
                onChange={handleChange}
                placeholder="Ejemplo: N"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Mínimas Unidades de Distribución"
                name="minimoDistri"
                value={formData.minimoDistri}
                onChange={handleChange}
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 2 }}>
            <Button type="submit" variant="contained" color="primary">
              Generar Reporte
            </Button>
          </Box>
        </Box>
      </Paper>

      {/* Tabla de reportes */}
      <Typography variant="h6" gutterBottom>
        Reportes de Distribución
      </Typography>
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Num Pedido</TableCell>
              <TableCell>Tipo Pedido</TableCell>
              <TableCell>Num Código</TableCell>
              <TableCell>Num Talla</TableCell>
              <TableCell>Cantidad Pedida</TableCell>
              <TableCell>Porcentaje</TableCell>
              <TableCell>Ciudad Destino</TableCell>
              <TableCell>Desc Marca</TableCell>
              <TableCell>Desc Familia</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reportData.map((row, index) => (
              <TableRow key={index}>
                <TableCell>{row.numPedido}</TableCell>
                <TableCell>{row.tipoPedido}</TableCell>
                <TableCell>{row.numCodigo}</TableCell>
                <TableCell>{row.numTalla}</TableCell>
                <TableCell>{row.cantidadPedida}</TableCell>
                <TableCell>{row.porcentaje}%</TableCell>
                <TableCell>{row.ciudadDestino}</TableCell>
                <TableCell>{row.descMarca}</TableCell>
                <TableCell>{row.descFamilia}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default Componente;