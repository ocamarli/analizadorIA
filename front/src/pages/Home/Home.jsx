import React from "react";
import { Grid, Box } from "@mui/material";
import Historias from "../Historias";

const Home = (props) => {
  return (
    <Grid
      container
      padding={1}
      alignItems="center"
      justifyContent="center"
      sx={{ opacity: ".7", minHeight: "50vh" }} // Agregado minHeight para centrado vertical
    >
      <Grid 
        item 
        xs={12}
        sx={{
          display: "flex",
          justifyContent: "center", // Centra horizontalmente
          alignItems: "center"      // Centra verticalmente
        }}
      >
        <Box
          component="img"
          sx={{
            height: 150,
            width: 'auto',
            
            objectFit: 'contain',
          }}
          alt="Logo"
          src="/CoppelLogo.png"
        />
      </Grid>
    </Grid>
  );
};

export default Home;