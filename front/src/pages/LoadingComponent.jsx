import React from 'react';
import { CircularProgress, Typography, Box } from '@mui/material';

const LoadingComponent = () => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      alignItems="center"
      justifyContent="center"
      height="100vh"
    >
      <CircularProgress />
      <Typography variant="h6" component="div" sx={{ mt: 2 }}>
        Cargando...
      </Typography>
    </Box>
  );
};

export default LoadingComponent;